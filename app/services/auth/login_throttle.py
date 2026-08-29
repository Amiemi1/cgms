from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import math
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
)
from typing import TypeAlias

from fastapi import Request
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db.models.security_models import (
    BrowserLoginThrottleRecord,
    SecurityLog,
)
from app.db.session import SessionLocal
from app.services.persistence.audit_store import (
    SECURITY_AUDIT,
    add_audit_record,
)


login_security_logger = logging.getLogger(
    "cgms.security.browser_login"
)

ANONYMOUS_SECURITY_ACTOR_ID = 0

LOGIN_FAILURE_ACTION = "browser_login_failure"
LOGIN_THROTTLED_ACTION = "browser_login_throttled"
LOGIN_SUCCESS_ACTION = "browser_login_success"

PAIR_SCOPE = "pair"
NETWORK_SCOPE = "network"

DEFAULT_WINDOW_SECONDS = 15 * 60
DEFAULT_PAIR_LIMIT = 5
DEFAULT_NETWORK_LIMIT = 25
DEFAULT_BLOCK_SECONDS = 15 * 60
DEFAULT_RETENTION_DAYS = 7

MAX_FORWARDED_HEADER_BYTES = 2048
MAX_FORWARDED_HOPS = 20

IpAddress: TypeAlias = IPv4Address | IPv6Address
IpNetwork: TypeAlias = IPv4Network | IPv6Network


class LoginThrottleError(RuntimeError):
    """
    Base exception for browser-login throttling failures.
    """


class LoginThrottleConfigurationError(
    LoginThrottleError
):
    """
    Raised when browser-login throttle configuration is unsafe.
    """


class LoginThrottlePersistenceError(
    LoginThrottleError
):
    """
    Raised when throttle state or its audit record cannot be
    persisted.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class LoginThrottleSettings:
    window_seconds: int
    pair_limit: int
    network_limit: int
    block_seconds: int
    retention_days: int
    trusted_proxy_networks: tuple[
        IpNetwork,
        ...,
    ]
    hmac_key: bytes


@dataclass(
    frozen=True,
    slots=True,
)
class LoginThrottleIdentity:
    pair_key: str
    network_key: str
    subject_audit_key: str
    network_audit_key: str


@dataclass(
    frozen=True,
    slots=True,
)
class LoginThrottleDecision:
    blocked: bool
    retry_after_seconds: int = 0
    blocked_scopes: tuple[str, ...] = ()

    @classmethod
    def allowed(cls) -> "LoginThrottleDecision":
        return cls(
            blocked=False,
            retry_after_seconds=0,
            blocked_scopes=(),
        )


def _read_bounded_integer(
    variable_name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        parsed_value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise LoginThrottleConfigurationError(
            f"{variable_name} must be an integer."
        ) from exc

    if not minimum <= parsed_value <= maximum:
        raise LoginThrottleConfigurationError(
            f"{variable_name} must be between "
            f"{minimum} and {maximum}."
        )

    return parsed_value


def _parse_trusted_proxy_networks(
    raw_value: str,
) -> tuple[IpNetwork, ...]:
    if not raw_value.strip():
        return ()

    networks: list[IpNetwork] = []

    for candidate in raw_value.split(","):
        normalized = candidate.strip()

        if not normalized:
            continue

        try:
            network = ipaddress.ip_network(
                normalized,
                strict=False,
            )
        except ValueError as exc:
            raise LoginThrottleConfigurationError(
                "CGMS_TRUSTED_PROXY_CIDRS contains "
                "an invalid network."
            ) from exc

        networks.append(network)

    return tuple(networks)


def get_login_throttle_settings(
) -> LoginThrottleSettings:
    secret = os.getenv(
        "CGMS_LOGIN_THROTTLE_SECRET",
        "",
    ).strip()

    if not secret:
        secret = os.getenv(
            "CGMS_JWT_SECRET",
            "",
        ).strip()

    if len(secret) < 32:
        raise LoginThrottleConfigurationError(
            "CGMS_LOGIN_THROTTLE_SECRET or "
            "CGMS_JWT_SECRET must contain at least "
            "32 characters."
        )

    # Derive a domain-specific key instead of using the JWT key
    # directly for login-identifier pseudonymisation.
    hmac_key = hmac.new(
        secret.encode("utf-8"),
        b"cgms-browser-login-throttle-v1",
        hashlib.sha256,
    ).digest()

    return LoginThrottleSettings(
        window_seconds=_read_bounded_integer(
            "CGMS_LOGIN_THROTTLE_WINDOW_SECONDS",
            default=DEFAULT_WINDOW_SECONDS,
            minimum=60,
            maximum=86_400,
        ),
        pair_limit=_read_bounded_integer(
            "CGMS_LOGIN_THROTTLE_PAIR_LIMIT",
            default=DEFAULT_PAIR_LIMIT,
            minimum=2,
            maximum=100,
        ),
        network_limit=_read_bounded_integer(
            "CGMS_LOGIN_THROTTLE_NETWORK_LIMIT",
            default=DEFAULT_NETWORK_LIMIT,
            minimum=5,
            maximum=1_000,
        ),
        block_seconds=_read_bounded_integer(
            "CGMS_LOGIN_THROTTLE_BLOCK_SECONDS",
            default=DEFAULT_BLOCK_SECONDS,
            minimum=60,
            maximum=86_400,
        ),
        retention_days=_read_bounded_integer(
            "CGMS_LOGIN_THROTTLE_RETENTION_DAYS",
            default=DEFAULT_RETENTION_DAYS,
            minimum=1,
            maximum=90,
        ),
        trusted_proxy_networks=(
            _parse_trusted_proxy_networks(
                os.getenv(
                    "CGMS_TRUSTED_PROXY_CIDRS",
                    "",
                )
            )
        ),
        hmac_key=hmac_key,
    )


def _as_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def _current_time(
    supplied_time: datetime | None,
) -> datetime:
    if supplied_time is None:
        return datetime.now(
            timezone.utc
        )

    return _as_utc(
        supplied_time
    )


def _normalize_email_for_throttle(
    email: str,
) -> str:
    if not isinstance(email, str):
        return "invalid-email"

    normalized = email.strip().casefold()

    if not normalized:
        return "blank-email"

    # The route already limits the full body. This additional
    # bound prevents unusually large identifiers entering the
    # HMAC input.
    return normalized[:320]


def _normalize_network_value(
    value: str,
) -> str:
    normalized = (
        value.strip().lower()
        if isinstance(value, str)
        else ""
    )

    if not normalized:
        return "unknown-network"

    try:
        address = ipaddress.ip_address(
            normalized
        )
    except ValueError:
        return f"host:{normalized[:255]}"

    if (
        isinstance(
            address,
            ipaddress.IPv6Address,
        )
        and address.ipv4_mapped is not None
    ):
        address = address.ipv4_mapped

    return address.compressed


def _address_in_networks(
    address: IpAddress,
    networks: tuple[IpNetwork, ...],
) -> bool:
    return any(
        address.version == network.version
        and address in network
        for network in networks
    )


def _parse_forwarded_address(
    value: str,
) -> IpAddress | None:
    normalized = value.strip()

    if (
        normalized.startswith("[")
        and "]" in normalized
    ):
        normalized = normalized[
            1:normalized.index("]")
        ]
    elif normalized.count(":") == 1:
        host, port = normalized.rsplit(
            ":",
            maxsplit=1,
        )

        if port.isdecimal():
            normalized = host

    try:
        address = ipaddress.ip_address(
            normalized
        )
    except ValueError:
        return None

    if (
        isinstance(
            address,
            ipaddress.IPv6Address,
        )
        and address.ipv4_mapped is not None
    ):
        address = address.ipv4_mapped

    return address


def resolve_client_network_identifier(
    request: Request,
    *,
    settings: LoginThrottleSettings,
) -> str:
    """
    Resolve the source network without trusting caller-supplied
    forwarding headers by default.

    X-Forwarded-For is considered only when the immediate peer is
    inside an explicitly configured trusted proxy network. The
    chain is walked from right to left and the first untrusted
    address is selected.
    """
    peer_host = (
        request.client.host
        if request.client is not None
        else ""
    )

    normalized_peer = _normalize_network_value(
        peer_host
    )

    peer_address = _parse_forwarded_address(
        peer_host
    )

    if (
        peer_address is None
        or not _address_in_networks(
            peer_address,
            settings.trusted_proxy_networks,
        )
    ):
        return normalized_peer

    forwarded_header = request.headers.get(
        "x-forwarded-for",
        "",
    )

    if (
        not forwarded_header
        or len(
            forwarded_header.encode(
                "utf-8",
                errors="ignore",
            )
        ) > MAX_FORWARDED_HEADER_BYTES
    ):
        return normalized_peer

    raw_hops = [
        item.strip()
        for item in forwarded_header.split(",")
        if item.strip()
    ]

    if (
        not raw_hops
        or len(raw_hops) > MAX_FORWARDED_HOPS
    ):
        return normalized_peer

    parsed_hops: list[
        IpAddress
    ] = []

    for raw_hop in raw_hops:
        parsed = _parse_forwarded_address(
            raw_hop
        )

        if parsed is None:
            return normalized_peer

        parsed_hops.append(parsed)

    chain = [
        *parsed_hops,
        peer_address,
    ]

    for address in reversed(chain):
        if not _address_in_networks(
            address,
            settings.trusted_proxy_networks,
        ):
            return address.compressed

    return parsed_hops[0].compressed


class BrowserLoginSecurityService:
    """
    Enforce persistent browser-login failure controls.

    Only HMAC-derived pseudonymous identifiers are stored. Raw
    email addresses, IP addresses, passwords, cookies and tokens
    are never written to the throttle table or SecurityLog.
    """

    def __init__(
        self,
        session_factory: Callable[
            [],
            Session,
        ] = SessionLocal,
        settings: LoginThrottleSettings | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings

    @property
    def settings(
        self,
    ) -> LoginThrottleSettings:
        if self._settings is None:
            self._settings = (
                get_login_throttle_settings()
            )

        return self._settings

    def resolve_network_identifier(
        self,
        request: Request,
    ) -> str:
        return resolve_client_network_identifier(
            request,
            settings=self.settings,
        )

    def _digest(
        self,
        label: str,
        value: str,
    ) -> str:
        message = (
            f"{label}\x00{value}"
            .encode(
                "utf-8",
                errors="strict",
            )
        )

        return hmac.new(
            self.settings.hmac_key,
            message,
            hashlib.sha256,
        ).hexdigest()

    def _build_identity(
        self,
        *,
        email: str,
        network_identifier: str,
    ) -> LoginThrottleIdentity:
        normalized_email = (
            _normalize_email_for_throttle(
                email
            )
        )

        normalized_network = (
            _normalize_network_value(
                network_identifier
            )
        )

        subject_key = self._digest(
            "subject",
            normalized_email,
        )

        network_key = self._digest(
            "network",
            normalized_network,
        )

        pair_key = self._digest(
            "pair",
            f"{subject_key}:{network_key}",
        )

        return LoginThrottleIdentity(
            pair_key=pair_key,
            network_key=network_key,
            subject_audit_key=subject_key[:16],
            network_audit_key=network_key[:16],
        )

    def _retry_after_for_record(
        self,
        record: BrowserLoginThrottleRecord,
        *,
        now: datetime,
    ) -> int:
        if record.blocked_until is None:
            return 0

        blocked_until = _as_utc(
            record.blocked_until
        )

        if blocked_until <= now:
            return 0

        return max(
            1,
            math.ceil(
                (
                    blocked_until - now
                ).total_seconds()
            ),
        )

    def _active_decision(
        self,
        records: list[
            BrowserLoginThrottleRecord
        ],
        *,
        now: datetime,
    ) -> LoginThrottleDecision:
        blocked_scopes: list[str] = []
        retry_after_seconds = 0

        for record in records:
            retry_after = (
                self._retry_after_for_record(
                    record,
                    now=now,
                )
            )

            if retry_after <= 0:
                continue

            blocked_scopes.append(
                record.scope
            )

            retry_after_seconds = max(
                retry_after_seconds,
                retry_after,
            )

        if not blocked_scopes:
            return LoginThrottleDecision.allowed()

        return LoginThrottleDecision(
            blocked=True,
            retry_after_seconds=(
                retry_after_seconds
            ),
            blocked_scopes=tuple(
                sorted(
                    set(blocked_scopes)
                )
            ),
        )

    def check(
        self,
        *,
        email: str,
        network_identifier: str,
        now: datetime | None = None,
    ) -> LoginThrottleDecision:
        checked_at = _current_time(
            now
        )

        identity = self._build_identity(
            email=email,
            network_identifier=(
                network_identifier
            ),
        )

        session: Session | None = None

        try:
            session = self._session_factory()
            records = session.exec(
                select(
                    BrowserLoginThrottleRecord
                ).where(
                    BrowserLoginThrottleRecord
                    .throttle_key.in_(
                        [
                            identity.pair_key,
                            identity.network_key,
                        ]
                    )
                )
            ).all()

            return self._active_decision(
                list(records),
                now=checked_at,
            )

        except Exception as exc:
            login_security_logger.exception(
                "browser_login_throttle_check_failed "
                "reason=persistence_failure"
            )

            raise LoginThrottlePersistenceError(
                "Browser login throttle state "
                "could not be checked."
            ) from exc

        finally:
            if session is not None:
                session.close()

    def _load_record_for_update(
        self,
        session: Session,
        *,
        throttle_key: str,
    ) -> BrowserLoginThrottleRecord | None:
        statement = (
            select(
                BrowserLoginThrottleRecord
            )
            .where(
                BrowserLoginThrottleRecord
                .throttle_key
                == throttle_key
            )
            .with_for_update()
        )

        return session.exec(
            statement
        ).first()

    def _advance_record(
        self,
        session: Session,
        *,
        throttle_key: str,
        scope: str,
        limit: int,
        failed_at: datetime,
    ) -> BrowserLoginThrottleRecord:
        record = self._load_record_for_update(
            session,
            throttle_key=throttle_key,
        )

        if record is None:
            record = BrowserLoginThrottleRecord(
                throttle_key=throttle_key,
                scope=scope,
                failure_count=1,
                window_started_at=failed_at,
                blocked_until=None,
                last_failure_at=failed_at,
                created_at=failed_at,
                updated_at=failed_at,
            )

            if limit <= 1:
                record.blocked_until = (
                    failed_at
                    + timedelta(
                        seconds=(
                            self.settings
                            .block_seconds
                        )
                    )
                )

            session.add(record)
            session.flush()

            return record

        window_started_at = _as_utc(
            record.window_started_at
        )

        window_ends_at = (
            window_started_at
            + timedelta(
                seconds=(
                    self.settings
                    .window_seconds
                )
            )
        )

        blocked_until = (
            _as_utc(record.blocked_until)
            if record.blocked_until is not None
            else None
        )

        if (
            blocked_until is not None
            and blocked_until > failed_at
        ):
            record.last_failure_at = failed_at
            record.updated_at = failed_at
            session.add(record)

            return record

        if failed_at >= window_ends_at:
            record.failure_count = 1
            record.window_started_at = (
                failed_at
            )
            record.blocked_until = None
        else:
            record.failure_count += 1

        record.last_failure_at = failed_at
        record.updated_at = failed_at

        if record.failure_count >= limit:
            record.blocked_until = (
                failed_at
                + timedelta(
                    seconds=(
                        self.settings
                        .block_seconds
                    )
                )
            )

        session.add(record)

        return record

    def _audit_details(
        self,
        *,
        identity: LoginThrottleIdentity,
        reason: str,
        decision: LoginThrottleDecision,
    ) -> str:
        return json.dumps(
            {
                "blocked": decision.blocked,
                "blocked_scopes": list(
                    decision.blocked_scopes
                ),
                "network_key": (
                    identity.network_audit_key
                ),
                "reason": reason,
                "retry_after_seconds": (
                    decision.retry_after_seconds
                ),
                "subject_key": (
                    identity.subject_audit_key
                ),
            },
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )

    def _record_failure_once(
        self,
        *,
        identity: LoginThrottleIdentity,
        reason: str,
        failed_at: datetime,
        network_only: bool,
    ) -> LoginThrottleDecision:
        session: Session | None = None

        try:
            session = self._session_factory()
            retention_cutoff = (
                failed_at
                - timedelta(
                    days=(
                        self.settings
                        .retention_days
                    )
                )
            )

            session.exec(
                delete(
                    BrowserLoginThrottleRecord
                ).where(
                    BrowserLoginThrottleRecord
                    .updated_at
                    < retention_cutoff
                )
            )

            records: list[
                BrowserLoginThrottleRecord
            ] = []

            if not network_only:
                records.append(
                    self._advance_record(
                        session,
                        throttle_key=(
                            identity.pair_key
                        ),
                        scope=PAIR_SCOPE,
                        limit=(
                            self.settings
                            .pair_limit
                        ),
                        failed_at=failed_at,
                    )
                )

            records.append(
                self._advance_record(
                    session,
                    throttle_key=(
                        identity.network_key
                    ),
                    scope=NETWORK_SCOPE,
                    limit=(
                        self.settings
                        .network_limit
                    ),
                    failed_at=failed_at,
                )
            )

            decision = self._active_decision(
                records,
                now=failed_at,
            )

            action = (
                LOGIN_THROTTLED_ACTION
                if decision.blocked
                else LOGIN_FAILURE_ACTION
            )
            audit_details = self._audit_details(
                identity=identity,
                reason=reason,
                decision=decision,
            )

            security_log = SecurityLog(
                user_id=(
                    ANONYMOUS_SECURITY_ACTOR_ID
                ),
                action=action,
                details=audit_details,
                created_at=failed_at,
            )
            session.add(
                security_log
            )
            session.flush()
            add_audit_record(
                session,
                category=SECURITY_AUDIT,
                action=action,
                source="browser_login_security",
                actor_id=(
                    ANONYMOUS_SECURITY_ACTOR_ID
                ),
                subject_type="login_identity",
                subject_id=(
                    identity.subject_audit_key
                ),
                outcome=(
                    "blocked"
                    if decision.blocked
                    else "denied"
                ),
                details=json.loads(
                    audit_details
                ),
                occurred_at=failed_at,
                origin_id=(
                    "legacy.security_log:"
                    f"{security_log.id}"
                ),
            )

            session.commit()

            login_security_logger.warning(
                "%s reason=%s blocked=%s "
                "blocked_scopes=%s "
                "subject_key=%s network_key=%s",
                action,
                reason,
                decision.blocked,
                ",".join(
                    decision.blocked_scopes
                )
                or "none",
                identity.subject_audit_key,
                identity.network_audit_key,
            )

            return decision

        except Exception:
            if session is not None:
                session.rollback()

            raise

        finally:
            if session is not None:
                session.close()

    def record_failure(
        self,
        *,
        email: str,
        network_identifier: str,
        reason: str = "authentication_failed",
        now: datetime | None = None,
        network_only: bool = False,
    ) -> LoginThrottleDecision:
        failed_at = _current_time(
            now
        )

        identity = self._build_identity(
            email=email,
            network_identifier=(
                network_identifier
            ),
        )

        for attempt in range(2):
            try:
                return self._record_failure_once(
                    identity=identity,
                    reason=reason,
                    failed_at=failed_at,
                    network_only=network_only,
                )
            except IntegrityError as exc:
                if attempt == 0:
                    continue

                login_security_logger.exception(
                    "browser_login_failure_record_failed "
                    "reason=concurrent_insert"
                )

                raise LoginThrottlePersistenceError(
                    "Browser login failure state "
                    "could not be persisted."
                ) from exc
            except Exception as exc:
                login_security_logger.exception(
                    "browser_login_failure_record_failed "
                    "reason=persistence_failure"
                )

                raise LoginThrottlePersistenceError(
                    "Browser login failure state "
                    "could not be persisted."
                ) from exc

        raise LoginThrottlePersistenceError(
            "Browser login failure state "
            "could not be persisted."
        )

    def record_invalid_request(
        self,
        *,
        network_identifier: str,
        now: datetime | None = None,
    ) -> LoginThrottleDecision:
        return self.record_failure(
            email="invalid-request",
            network_identifier=(
                network_identifier
            ),
            reason="invalid_request",
            now=now,
            network_only=True,
        )

    def record_success(
        self,
        *,
        email: str,
        network_identifier: str,
        user_id: int,
        workspace_id: str | None = None,
        now: datetime | None = None,
    ) -> None:
        succeeded_at = _current_time(
            now
        )

        identity = self._build_identity(
            email=email,
            network_identifier=(
                network_identifier
            ),
        )

        session: Session | None = None

        try:
            session = self._session_factory()
            pair_record = (
                self._load_record_for_update(
                    session,
                    throttle_key=(
                        identity.pair_key
                    ),
                )
            )

            if pair_record is not None:
                session.delete(
                    pair_record
                )

            details = json.dumps(
                {
                    "network_key": (
                        identity.network_audit_key
                    ),
                    "subject_key": (
                        identity.subject_audit_key
                    ),
                },
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
            )

            security_log = SecurityLog(
                user_id=user_id,
                workspace_id=workspace_id,
                action=LOGIN_SUCCESS_ACTION,
                details=details,
                created_at=succeeded_at,
            )
            session.add(
                security_log
            )
            session.flush()
            add_audit_record(
                session,
                category=SECURITY_AUDIT,
                action=LOGIN_SUCCESS_ACTION,
                source="browser_login_security",
                workspace_id=workspace_id,
                actor_id=user_id,
                subject_type="account",
                subject_id=user_id,
                outcome="authenticated",
                details=json.loads(
                    details
                ),
                occurred_at=succeeded_at,
                origin_id=(
                    "legacy.security_log:"
                    f"{security_log.id}"
                ),
            )

            session.commit()

            login_security_logger.info(
                "browser_login_success "
                "user_id=%s subject_key=%s "
                "network_key=%s",
                user_id,
                identity.subject_audit_key,
                identity.network_audit_key,
            )

        except Exception as exc:
            if session is not None:
                session.rollback()

            login_security_logger.exception(
                "browser_login_success_record_failed "
                "user_id=%s reason=persistence_failure",
                user_id,
            )

            raise LoginThrottlePersistenceError(
                "Browser login success state "
                "could not be persisted."
            ) from exc

        finally:
            if session is not None:
                session.close()
