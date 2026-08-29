from __future__ import annotations

import json
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest
from fastapi import Request
from sqlalchemy.pool import StaticPool
from sqlmodel import (
    SQLModel,
    Session,
    create_engine,
    select,
)

from app.db.models.security_models import (
    BrowserLoginThrottleRecord,
    SecurityLog,
)
from app.db.models.audit_record import AuditRecord
from app.services.auth.login_throttle import (
    LOGIN_FAILURE_ACTION,
    LOGIN_SUCCESS_ACTION,
    LOGIN_THROTTLED_ACTION,
    BrowserLoginSecurityService,
    LoginThrottleConfigurationError,
    LoginThrottlePersistenceError,
    LoginThrottleSettings,
    get_login_throttle_settings,
    resolve_client_network_identifier,
)


BASE_TIME = datetime(
    2026,
    7,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)

TEST_HMAC_KEY = b"x" * 32


@pytest.fixture()
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(
        test_engine
    )

    return test_engine


def build_settings(
    *,
    pair_limit: int = 3,
    network_limit: int = 10,
    window_seconds: int = 300,
    block_seconds: int = 120,
    trusted_proxy_networks=(),
) -> LoginThrottleSettings:
    return LoginThrottleSettings(
        window_seconds=window_seconds,
        pair_limit=pair_limit,
        network_limit=network_limit,
        block_seconds=block_seconds,
        retention_days=7,
        trusted_proxy_networks=tuple(
            trusted_proxy_networks
        ),
        hmac_key=TEST_HMAC_KEY,
    )


def create_service(
    engine,
    *,
    settings: LoginThrottleSettings | None = None,
) -> BrowserLoginSecurityService:
    return BrowserLoginSecurityService(
        session_factory=lambda: Session(
            engine
        ),
        settings=settings or build_settings(),
    )


def load_throttle_records(
    engine,
) -> list[BrowserLoginThrottleRecord]:
    with Session(engine) as session:
        records = session.exec(
            select(
                BrowserLoginThrottleRecord
            ).order_by(
                BrowserLoginThrottleRecord.id
            )
        ).all()

        for record in records:
            session.expunge(record)

        return list(records)


def load_security_logs(
    engine,
) -> list[SecurityLog]:
    with Session(engine) as session:
        records = session.exec(
            select(SecurityLog).order_by(
                SecurityLog.id
            )
        ).all()

        for record in records:
            session.expunge(record)

        return list(records)


def load_unified_audit_records(
    engine,
) -> list[AuditRecord]:
    with Session(engine) as session:
        records = session.exec(
            select(AuditRecord).order_by(
                AuditRecord.id
            )
        ).all()

        for record in records:
            session.expunge(record)

        return list(records)


def build_request(
    *,
    peer_host: str,
    forwarded_for: str | None = None,
) -> Request:
    headers: list[
        tuple[bytes, bytes]
    ] = []

    if forwarded_for is not None:
        headers.append(
            (
                b"x-forwarded-for",
                forwarded_for.encode("ascii"),
            )
        )

    return Request(
        {
            "type": "http",
            "asgi": {
                "version": "3.0",
                "spec_version": "2.3",
            },
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/auth/login",
            "raw_path": b"/auth/login",
            "query_string": b"",
            "headers": headers,
            "client": (
                peer_host,
                44321,
            ),
            "server": (
                "testserver",
                443,
            ),
        }
    )


def test_failure_state_uses_only_pseudonymous_identifiers(
    engine,
) -> None:
    service = create_service(engine)

    service.record_failure(
        email="Sensitive.User@example.com",
        network_identifier="203.0.113.25",
        now=BASE_TIME,
    )

    records = load_throttle_records(
        engine
    )

    assert len(records) == 2

    assert {
        record.scope
        for record in records
    } == {
        "pair",
        "network",
    }

    for record in records:
        assert len(record.throttle_key) == 64
        assert (
            "Sensitive.User@example.com"
            not in record.throttle_key
        )
        assert (
            "203.0.113.25"
            not in record.throttle_key
        )

    logs = load_security_logs(engine)

    assert len(logs) == 1
    assert logs[0].action == LOGIN_FAILURE_ACTION
    assert logs[0].user_id == 0
    assert logs[0].details is not None

    assert (
        "Sensitive.User@example.com"
        not in logs[0].details
    )
    assert "203.0.113.25" not in logs[0].details
    assert "password" not in logs[0].details
    assert "cookie" not in logs[0].details
    assert "token" not in logs[0].details


def test_pair_threshold_blocks_and_sets_retry_after(
    engine,
) -> None:
    service = create_service(engine)

    first = service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=BASE_TIME,
    )

    second = service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=(
            BASE_TIME
            + timedelta(seconds=1)
        ),
    )

    third = service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=(
            BASE_TIME
            + timedelta(seconds=2)
        ),
    )

    assert not first.blocked
    assert not second.blocked
    assert third.blocked
    assert third.blocked_scopes == ("pair",)
    assert third.retry_after_seconds == 120

    assert (
        load_security_logs(engine)[-1].action
        == LOGIN_THROTTLED_ACTION
    )


def test_preflight_check_rejects_active_block(
    engine,
) -> None:
    service = create_service(engine)

    for offset in range(3):
        service.record_failure(
            email="user@example.com",
            network_identifier="203.0.113.10",
            now=(
                BASE_TIME
                + timedelta(seconds=offset)
            ),
        )

    decision = service.check(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=(
            BASE_TIME
            + timedelta(seconds=10)
        ),
    )

    assert decision.blocked
    assert decision.blocked_scopes == ("pair",)
    assert decision.retry_after_seconds == 112


def test_window_resets_after_expiry(
    engine,
) -> None:
    service = create_service(
        engine,
        settings=build_settings(
            pair_limit=3,
            window_seconds=60,
            block_seconds=120,
        ),
    )

    service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=BASE_TIME,
    )

    service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=(
            BASE_TIME
            + timedelta(seconds=10)
        ),
    )

    decision = service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=(
            BASE_TIME
            + timedelta(seconds=61)
        ),
    )

    assert not decision.blocked

    pair_record = next(
        record
        for record in load_throttle_records(
            engine
        )
        if record.scope == "pair"
    )

    assert pair_record.failure_count == 1


def test_network_threshold_aggregates_different_subjects(
    engine,
) -> None:
    service = create_service(
        engine,
        settings=build_settings(
            pair_limit=10,
            network_limit=3,
        ),
    )

    decisions = [
        service.record_failure(
            email=f"user-{index}@example.com",
            network_identifier="203.0.113.44",
            now=(
                BASE_TIME
                + timedelta(seconds=index)
            ),
        )
        for index in range(3)
    ]

    assert not decisions[0].blocked
    assert not decisions[1].blocked
    assert decisions[2].blocked
    assert (
        decisions[2].blocked_scopes
        == ("network",)
    )


def test_success_clears_pair_state_but_preserves_network_state(
    engine,
) -> None:
    service = create_service(engine)

    service.record_failure(
        email="user@example.com",
        network_identifier="203.0.113.10",
        now=BASE_TIME,
    )

    service.record_success(
        email="user@example.com",
        network_identifier="203.0.113.10",
        user_id=1001,
        now=(
            BASE_TIME
            + timedelta(seconds=2)
        ),
    )

    records = load_throttle_records(
        engine
    )

    assert len(records) == 1
    assert records[0].scope == "network"
    assert records[0].failure_count == 1

    logs = load_security_logs(engine)

    assert logs[-1].action == LOGIN_SUCCESS_ACTION
    assert logs[-1].user_id == 1001

    details = json.loads(
        logs[-1].details or "{}"
    )

    assert set(details) == {
        "network_key",
        "subject_key",
    }

    unified = load_unified_audit_records(
        engine
    )[-1]
    assert unified.category == "security"
    assert unified.action == LOGIN_SUCCESS_ACTION
    assert unified.actor_id == "1001"
    assert unified.details == details


def test_invalid_request_updates_only_network_scope(
    engine,
) -> None:
    service = create_service(engine)

    service.record_invalid_request(
        network_identifier="203.0.113.10",
        now=BASE_TIME,
    )

    records = load_throttle_records(
        engine
    )

    assert len(records) == 1
    assert records[0].scope == "network"

    details = json.loads(
        load_security_logs(engine)[0].details
        or "{}"
    )

    assert details["reason"] == "invalid_request"


def test_untrusted_peer_cannot_spoof_forwarded_header(
) -> None:
    settings = build_settings(
        trusted_proxy_networks=(),
    )

    request = build_request(
        peer_host="198.51.100.7",
        forwarded_for="203.0.113.8",
    )

    assert resolve_client_network_identifier(
        request,
        settings=settings,
    ) == "198.51.100.7"


def test_trusted_proxy_chain_resolves_first_untrusted_client(
) -> None:
    import ipaddress

    settings = build_settings(
        trusted_proxy_networks=(
            ipaddress.ip_network(
                "10.0.0.0/8"
            ),
            ipaddress.ip_network(
                "192.0.2.0/24"
            ),
        ),
    )

    request = build_request(
        peer_host="10.0.0.5",
        forwarded_for=(
            "203.0.113.8, 192.0.2.20"
        ),
    )

    assert resolve_client_network_identifier(
        request,
        settings=settings,
    ) == "203.0.113.8"


def test_malformed_forwarded_chain_falls_back_to_peer(
) -> None:
    import ipaddress

    settings = build_settings(
        trusted_proxy_networks=(
            ipaddress.ip_network(
                "10.0.0.0/8"
            ),
        ),
    )

    request = build_request(
        peer_host="10.0.0.5",
        forwarded_for="not-an-ip",
    )

    assert resolve_client_network_identifier(
        request,
        settings=settings,
    ) == "10.0.0.5"


def test_configuration_requires_long_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "CGMS_LOGIN_THROTTLE_SECRET",
        raising=False,
    )

    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        "too-short",
    )

    with pytest.raises(
        LoginThrottleConfigurationError,
        match="32 characters",
    ):
        get_login_throttle_settings()


def test_configuration_rejects_invalid_proxy_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_LOGIN_THROTTLE_SECRET",
        "x" * 40,
    )

    monkeypatch.setenv(
        "CGMS_TRUSTED_PROXY_CIDRS",
        "not-a-network",
    )

    with pytest.raises(
        LoginThrottleConfigurationError,
        match="invalid network",
    ):
        get_login_throttle_settings()


def test_persistence_failure_fails_closed(
) -> None:
    def broken_session_factory():
        raise RuntimeError(
            "database unavailable"
        )

    service = BrowserLoginSecurityService(
        session_factory=(
            broken_session_factory
        ),
        settings=build_settings(),
    )

    with pytest.raises(
        LoginThrottlePersistenceError,
    ):
        service.check(
            email="user@example.com",
            network_identifier="203.0.113.10",
            now=BASE_TIME,
        )


def test_failure_record_session_factory_failure_fails_closed(
) -> None:
    def broken_session_factory():
        raise RuntimeError(
            "database unavailable"
        )

    service = BrowserLoginSecurityService(
        session_factory=(
            broken_session_factory
        ),
        settings=build_settings(),
    )

    with pytest.raises(
        LoginThrottlePersistenceError,
    ):
        service.record_failure(
            email="user@example.com",
            network_identifier="203.0.113.10",
            now=BASE_TIME,
        )


def test_success_record_session_factory_failure_fails_closed(
) -> None:
    def broken_session_factory():
        raise RuntimeError(
            "database unavailable"
        )

    service = BrowserLoginSecurityService(
        session_factory=(
            broken_session_factory
        ),
        settings=build_settings(),
    )

    with pytest.raises(
        LoginThrottlePersistenceError,
    ):
        service.record_success(
            email="user@example.com",
            network_identifier="203.0.113.10",
            user_id=42,
            now=BASE_TIME,
        )
