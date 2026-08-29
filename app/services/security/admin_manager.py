from sqlmodel import select
from app.db.models.security_models import UserRole
from app.services.persistence.audit_store import (
    GOVERNANCE_AUDIT,
    add_audit_record,
)


# ------------------------------------------------
# ADD ADMIN
# ------------------------------------------------

def add_admin(
    session,
    user_id: int,
    *,
    actor_user_id: int | None = None,
):

    existing = session.exec(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role == "admin"
        )
    ).first()

    if existing:
        return False

    role = UserRole(
        user_id=user_id,
        role="admin"
    )

    session.add(role)
    add_audit_record(
        session,
        category=GOVERNANCE_AUDIT,
        action="admin_added",
        source="telegram_security_handler",
        actor_id=(
            actor_user_id
            if actor_user_id is not None
            else user_id
        ),
        subject_type="account_role",
        subject_id=user_id,
        outcome="changed",
        details={
            "role": "admin",
        },
    )
    session.commit()

    return True


# ------------------------------------------------
# REMOVE ADMIN
# ------------------------------------------------

def remove_admin(
    session,
    user_id: int,
    *,
    actor_user_id: int | None = None,
):

    role = session.exec(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role == "admin"
        )
    ).first()

    if not role:
        return False

    session.delete(role)
    add_audit_record(
        session,
        category=GOVERNANCE_AUDIT,
        action="admin_removed",
        source="telegram_security_handler",
        actor_id=(
            actor_user_id
            if actor_user_id is not None
            else user_id
        ),
        subject_type="account_role",
        subject_id=user_id,
        outcome="changed",
        details={
            "role": "admin",
        },
    )
    session.commit()

    return True


# ------------------------------------------------
# CHECK ADMIN
# ------------------------------------------------

def is_admin(session, user_id: int):

    role = session.exec(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role == "admin"
        )
    ).first()

    return role is not None
