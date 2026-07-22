from __future__ import annotations

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
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
)
from app.services.auth.session_registry import (
    BrowserSessionExpiredError,
    BrowserSessionNotRegisteredError,
    BrowserSessionRecordConflictError,
    BrowserSessionRecordMismatchError,
    BrowserSessionRegistry,
    BrowserSessionRevocationReasonError,
    BrowserSessionRevokedError,
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


def create_registry(
    engine,
) -> BrowserSessionRegistry:
    return BrowserSessionRegistry(
        session_factory=lambda: Session(
            engine
        )
    )


def build_identity(
    *,
    token_id: str = "session-token-1001",
    user_id: str = "1001",
    role: str = "operator",
    issued_at: datetime = BASE_TIME,
    expires_at: datetime | None = None,
) -> BrowserSessionIdentity:
    return BrowserSessionIdentity(
        user_id=user_id,
        role=role,
        token_id=token_id,
        issued_at=issued_at,
        expires_at=(
            expires_at
            if expires_at is not None
            else issued_at
            + timedelta(minutes=30)
        ),
    )


def test_registers_active_session(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    state = registry.register(
        build_identity(),
        now=BASE_TIME,
    )

    assert state.token_id == (
        "session-token-1001"
    )
    assert state.user_id == 1001
    assert state.role == "operator"
    assert state.is_revoked is False

    assert state.is_active_at(
        BASE_TIME
        + timedelta(minutes=1)
    )


def test_registration_is_idempotent(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    first = registry.register(
        identity,
        now=BASE_TIME,
    )

    second = registry.register(
        identity,
        now=BASE_TIME,
    )

    assert first == second

    with Session(engine) as session:
        records = session.exec(
            select(BrowserSessionRecord)
        ).all()

    assert len(records) == 1


def test_conflicting_token_id_is_rejected(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    registry.register(
        build_identity(),
        now=BASE_TIME,
    )

    conflicting = build_identity(
        user_id="2001",
    )

    with pytest.raises(
        BrowserSessionRecordConflictError
    ):
        registry.register(
            conflicting,
            now=BASE_TIME,
        )


def test_expired_session_cannot_be_registered(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    with pytest.raises(
        BrowserSessionExpiredError
    ):
        registry.register(
            build_identity(
                expires_at=BASE_TIME,
            ),
            now=BASE_TIME,
        )


def test_unregistered_session_is_denied(
    engine,
) -> None:
    with pytest.raises(
        BrowserSessionNotRegisteredError
    ):
        create_registry(
            engine
        ).require_active(
            build_identity(),
            now=BASE_TIME,
        )


def test_active_session_is_validated(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    registry.register(
        identity,
        now=BASE_TIME,
    )

    state = registry.require_active(
        identity,
        now=(
            BASE_TIME
            + timedelta(minutes=10)
        ),
    )

    assert state.is_active_at(
        BASE_TIME
        + timedelta(minutes=10)
    )


def test_user_mismatch_is_denied(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    registry.register(
        build_identity(),
        now=BASE_TIME,
    )

    with pytest.raises(
        BrowserSessionRecordMismatchError
    ):
        registry.require_active(
            build_identity(
                user_id="2001"
            ),
            now=BASE_TIME,
        )


def test_role_mismatch_is_denied(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    registry.register(
        build_identity(),
        now=BASE_TIME,
    )

    with pytest.raises(
        BrowserSessionRecordMismatchError
    ):
        registry.require_active(
            build_identity(
                role="admin"
            ),
            now=BASE_TIME,
        )


def test_issued_at_mismatch_is_denied(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    registry.register(
        build_identity(),
        now=BASE_TIME,
    )

    with pytest.raises(
        BrowserSessionRecordMismatchError
    ):
        registry.require_active(
            build_identity(
                issued_at=(
                    BASE_TIME
                    + timedelta(seconds=1)
                )
            ),
            now=BASE_TIME,
        )


def test_expiry_mismatch_is_denied(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    registry.register(
        build_identity(),
        now=BASE_TIME,
    )

    with pytest.raises(
        BrowserSessionRecordMismatchError
    ):
        registry.require_active(
            build_identity(
                expires_at=(
                    BASE_TIME
                    + timedelta(minutes=60)
                )
            ),
            now=BASE_TIME,
        )


def test_expired_record_is_denied(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    registry.register(
        identity,
        now=BASE_TIME,
    )

    with pytest.raises(
        BrowserSessionExpiredError
    ):
        registry.require_active(
            identity,
            now=(
                BASE_TIME
                + timedelta(minutes=30)
            ),
        )


def test_revoke_marks_session_revoked(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    registry.register(
        identity,
        now=BASE_TIME,
    )

    state = registry.revoke(
        identity,
        reason="logout",
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    assert state.is_revoked is True
    assert state.revocation_reason == "logout"

    with pytest.raises(
        BrowserSessionRevokedError
    ):
        registry.require_active(
            identity,
            now=(
                BASE_TIME
                + timedelta(minutes=6)
            ),
        )


def test_revoke_is_idempotent(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    registry.register(
        identity,
        now=BASE_TIME,
    )

    first = registry.revoke(
        identity,
        now=(
            BASE_TIME
            + timedelta(minutes=1)
        ),
    )

    second = registry.revoke(
        identity,
        now=(
            BASE_TIME
            + timedelta(minutes=2)
        ),
    )

    assert (
        second.revoked_at
        == first.revoked_at
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
def test_invalid_revocation_reason_is_rejected(
    engine,
    reason: str,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    registry.register(
        identity,
        now=BASE_TIME,
    )

    with pytest.raises(
        BrowserSessionRevocationReasonError
    ):
        registry.revoke(
            identity,
            reason=reason,
            now=BASE_TIME,
        )


def test_revoked_session_cannot_be_registered_again(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    identity = build_identity()

    registry.register(
        identity,
        now=BASE_TIME,
    )

    registry.revoke(
        identity,
        now=(
            BASE_TIME
            + timedelta(minutes=1)
        ),
    )

    with pytest.raises(
        BrowserSessionRecordConflictError
    ):
        registry.register(
            identity,
            now=(
                BASE_TIME
                + timedelta(minutes=2)
            ),
        )


def test_revoke_all_revokes_active_user_sessions(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    first = build_identity(
        token_id="session-one",
    )

    second = build_identity(
        token_id="session-two",
    )

    other_user = build_identity(
        token_id="session-other-user",
        user_id="2001",
    )

    registry.register(
        first,
        now=BASE_TIME,
    )

    registry.register(
        second,
        now=BASE_TIME,
    )

    registry.register(
        other_user,
        now=BASE_TIME,
    )

    count = registry.revoke_all_for_user(
        1001,
        reason="admin_revocation",
        revoked_by_user_id=9001,
        now=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    assert count == 2

    with pytest.raises(
        BrowserSessionRevokedError
    ):
        registry.require_active(
            first,
            now=(
                BASE_TIME
                + timedelta(minutes=6)
            ),
        )

    with pytest.raises(
        BrowserSessionRevokedError
    ):
        registry.require_active(
            second,
            now=(
                BASE_TIME
                + timedelta(minutes=6)
            ),
        )

    assert registry.require_active(
        other_user,
        now=(
            BASE_TIME
            + timedelta(minutes=6)
        ),
    ).is_revoked is False


def test_revoke_all_ignores_expired_sessions(
    engine,
) -> None:
    registry = create_registry(
        engine
    )

    expired_later = build_identity(
        token_id="expires-soon",
        expires_at=(
            BASE_TIME
            + timedelta(minutes=5)
        ),
    )

    active = build_identity(
        token_id="remains-active",
    )

    registry.register(
        expired_later,
        now=BASE_TIME,
    )

    registry.register(
        active,
        now=BASE_TIME,
    )

    count = registry.revoke_all_for_user(
        1001,
        now=(
            BASE_TIME
            + timedelta(minutes=10)
        ),
    )

    assert count == 1


def test_raw_token_is_not_a_database_column() -> None:
    column_names = {
        column.name
        for column
        in BrowserSessionRecord.__table__.columns
    }

    assert "token" not in column_names
    assert "jwt" not in column_names
    assert "cookie" not in column_names
    assert "token_id" in column_names