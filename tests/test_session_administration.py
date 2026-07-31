from __future__ import annotations

import json
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import (
    SQLModel,
    Session,
    create_engine,
    select,
)

from app.db.models.security_models import (
    BrowserSessionRecord,
    SecurityLog,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.security.rbac_policy import (
    MANAGE_BROWSER_SESSIONS,
    get_permissions,
)
from app.services.security.session_administration import (
    ADMIN_SESSION_REVOCATION_ACTION,
    SessionAdministrationInputError,
    SessionAdministrationPermissionError,
    SessionAdministrationService,
)


BASE_TIME = datetime(
    2026,
    7,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)


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


def create_service(
    engine,
) -> SessionAdministrationService:
    return SessionAdministrationService(
        session_factory=lambda: Session(
            engine
        )
    )


def build_principal(
    *,
    role: str = "admin",
    user_id: str = "9001",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        workspace_id="default",
        user_id=user_id,
        role=role,
        permissions=get_permissions(
            role
        ),
        token_id=(
            "administrator-session-token"
        ),
    )


def add_session(
    engine,
    *,
    token_id: str,
    user_id: int,
    expires_at: datetime,
    revoked_at: datetime | None = None,
) -> None:
    with Session(engine) as session:
        session.add(
            BrowserSessionRecord(
                token_id=token_id,
                user_id=user_id,
                role="operator",
                issued_at=BASE_TIME,
                expires_at=expires_at,
                revoked_at=revoked_at,
            )
        )

        session.commit()


def load_session_record(
    engine,
    token_id: str,
) -> BrowserSessionRecord:
    with Session(engine) as session:
        record = session.exec(
            select(
                BrowserSessionRecord
            ).where(
                BrowserSessionRecord.token_id
                == token_id
            )
        ).one()

        session.expunge(
            record
        )

        return record


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
            session.expunge(
                record
            )

        return list(records)


def test_admin_has_session_management_permission(
) -> None:
    assert (
        MANAGE_BROWSER_SESSIONS
        in get_permissions("admin")
    )


@pytest.mark.parametrize(
    "role",
    [
        "operator",
        "viewer",
        "unknown",
        "",
    ],
)
def test_non_admin_roles_lack_session_management_permission(
    role: str,
) -> None:
    assert (
        MANAGE_BROWSER_SESSIONS
        not in get_permissions(role)
    )


def test_admin_revokes_all_active_target_sessions(
    engine,
) -> None:
    add_session(
        engine,
        token_id="target-one",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=30)
        ),
    )

    add_session(
        engine,
        token_id="target-two",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=45)
        ),
    )

    add_session(
        engine,
        token_id="other-user",
        user_id=2001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=30)
        ),
    )

    result = create_service(
        engine
    ).revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    assert result.actor_user_id == 9001
    assert result.target_user_id == 1001
    assert result.revoked_count == 2
    assert result.sessions_were_revoked
    assert result.reason == "admin_revocation"

    first = load_session_record(
        engine,
        "target-one",
    )

    second = load_session_record(
        engine,
        "target-two",
    )

    other = load_session_record(
        engine,
        "other-user",
    )

    assert first.revoked_at is not None
    assert second.revoked_at is not None

    assert (
        first.revoked_by_user_id
        == 9001
    )

    assert (
        second.revoked_by_user_id
        == 9001
    )

    assert (
        first.revocation_reason
        == "admin_revocation"
    )

    assert (
        second.revocation_reason
        == "admin_revocation"
    )

    assert other.revoked_at is None


def test_expired_sessions_are_not_rewritten(
    engine,
) -> None:
    add_session(
        engine,
        token_id="expired-target",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=2)
        ),
    )

    result = create_service(
        engine
    ).revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    assert result.revoked_count == 0

    record = load_session_record(
        engine,
        "expired-target",
    )

    assert record.revoked_at is None


def test_existing_revoked_sessions_are_not_rewritten(
    engine,
) -> None:
    original_revocation_time = (
        BASE_TIME
        + timedelta(minutes=1)
    )

    add_session(
        engine,
        token_id="already-revoked",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=30)
        ),
        revoked_at=(
            original_revocation_time
        ),
    )

    result = create_service(
        engine
    ).revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    assert result.revoked_count == 0

    record = load_session_record(
        engine,
        "already-revoked",
    )

    assert (
        record.revoked_at.replace(
            tzinfo=timezone.utc
        )
        == original_revocation_time
    )


def test_revocation_creates_actor_attributed_audit_log(
    engine,
) -> None:
    add_session(
        engine,
        token_id="audit-target",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=30)
        ),
    )

    create_service(
        engine
    ).revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        reason="security_incident",
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    logs = load_security_logs(
        engine
    )

    assert len(logs) == 1

    log = logs[0]

    assert log.user_id == 9001

    assert (
        log.action
        == ADMIN_SESSION_REVOCATION_ACTION
    )

    assert log.details is not None

    details = json.loads(
        log.details
    )

    assert details == {
        "actor_user_id": 9001,
        "reason": "security_incident",
        "revoked_count": 1,
        "target_user_id": 1001,
    }

    assert "token" not in log.details
    assert "cookie" not in log.details
    assert "password" not in log.details
    assert "email" not in log.details


def test_zero_result_still_creates_audit_record(
    engine,
) -> None:
    result = create_service(
        engine
    ).revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        now=BASE_TIME,
    )

    assert result.revoked_count == 0

    logs = load_security_logs(
        engine
    )

    assert len(logs) == 1

    details = json.loads(
        logs[0].details or "{}"
    )

    assert details["revoked_count"] == 0


@pytest.mark.parametrize(
    "role",
    [
        "operator",
        "viewer",
    ],
)
def test_non_admin_actor_is_denied(
    engine,
    role: str,
) -> None:
    add_session(
        engine,
        token_id=f"{role}-denied-target",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=30)
        ),
    )

    service = create_service(
        engine
    )

    with pytest.raises(
        SessionAdministrationPermissionError,
        match="permission",
    ):
        service.revoke_user_sessions(
            actor=build_principal(
                role=role
            ),
            target_user_id=1001,
            now=BASE_TIME,
        )

    record = load_session_record(
        engine,
        f"{role}-denied-target",
    )

    assert record.revoked_at is None

    assert load_security_logs(
        engine
    ) == []


@pytest.mark.parametrize(
    "target_user_id",
    [
        "",
        " ",
        "not-a-number",
        "0",
        "-1",
    ],
)
def test_invalid_target_identifier_is_rejected(
    engine,
    target_user_id: str,
) -> None:
    with pytest.raises(
        SessionAdministrationInputError,
        match="target user identifier",
    ):
        create_service(
            engine
        ).revoke_user_sessions(
            actor=build_principal(),
            target_user_id=(
                target_user_id
            ),
            now=BASE_TIME,
        )


@pytest.mark.parametrize(
    "actor_user_id",
    [
        "",
        " ",
        "not-a-number",
        "0",
        "-1",
    ],
)
def test_invalid_actor_identifier_is_rejected(
    engine,
    actor_user_id: str,
) -> None:
    with pytest.raises(
        SessionAdministrationInputError,
        match="actor user identifier",
    ):
        create_service(
            engine
        ).revoke_user_sessions(
            actor=build_principal(
                user_id=actor_user_id
            ),
            target_user_id=1001,
            now=BASE_TIME,
        )


@pytest.mark.parametrize(
    "reason",
    [
        "",
        " ",
        "Contains Spaces",
        "contains/slash",
        "x" * 65,
    ],
)
def test_invalid_reason_is_rejected(
    engine,
    reason: str,
) -> None:
    with pytest.raises(
        SessionAdministrationInputError,
        match="revocation reason",
    ):
        create_service(
            engine
        ).revoke_user_sessions(
            actor=build_principal(),
            target_user_id=1001,
            reason=reason,
            now=BASE_TIME,
        )


def test_repeated_administrative_revocation_is_idempotent(
    engine,
) -> None:
    add_session(
        engine,
        token_id="idempotent-target",
        user_id=1001,
        expires_at=(
            BASE_TIME
            + timedelta(minutes=30)
        ),
    )

    service = create_service(
        engine
    )

    first = service.revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    second = service.revoke_user_sessions(
        actor=build_principal(),
        target_user_id=1001,
        now=(
            BASE_TIME
            + timedelta(minutes=6)
        ),
    )

    assert first.revoked_count == 1
    assert second.revoked_count == 0

    logs = load_security_logs(
        engine
    )

    assert len(logs) == 2
