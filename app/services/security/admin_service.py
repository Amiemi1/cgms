from sqlmodel import select

from app.db.models import UserRole, SecurityLog
from app.services.persistence.audit_store import (
    GOVERNANCE_AUDIT,
    add_audit_record,
)


# ------------------------------------------------
# CHECK IF USER IS ADMIN
# ------------------------------------------------

def is_admin(session, user_id: int) -> bool:

    role = session.exec(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role == "admin"
        )
    ).first()

    return role is not None


# ------------------------------------------------
# ADD ADMIN
# ------------------------------------------------

def add_admin(session, user_id: int):

    existing = session.exec(
        select(UserRole).where(UserRole.user_id == user_id)
    ).first()

    if existing:
        existing.role = "admin"
    else:
        role = UserRole(
            user_id=user_id,
            role="admin"
        )
        session.add(role)

    log = SecurityLog(
        user_id=user_id,
        action="admin_added",
        details="User granted admin privileges"
    )

    session.add(log)
    session.flush()
    add_audit_record(
        session,
        category=GOVERNANCE_AUDIT,
        action="admin_added",
        source="security_admin_service",
        actor_id=user_id,
        subject_type="account_role",
        subject_id=user_id,
        outcome="changed",
        details={
            "message": "User granted admin privileges",
        },
        origin_id=(
            "legacy.security_log:"
            f"{log.id}"
        ),
    )
    session.commit()


# ------------------------------------------------
# REMOVE ADMIN
# ------------------------------------------------

def remove_admin(session, user_id: int):

    role = session.exec(
        select(UserRole).where(UserRole.user_id == user_id)
    ).first()

    if role:
        session.delete(role)

    log = SecurityLog(
        user_id=user_id,
        action="admin_removed",
        details="Admin privileges revoked"
    )

    session.add(log)
    session.flush()
    add_audit_record(
        session,
        category=GOVERNANCE_AUDIT,
        action="admin_removed",
        source="security_admin_service",
        actor_id=user_id,
        subject_type="account_role",
        subject_id=user_id,
        outcome="changed",
        details={
            "message": "Admin privileges revoked",
        },
        origin_id=(
            "legacy.security_log:"
            f"{log.id}"
        ),
    )
    session.commit()


# ------------------------------------------------
# LIST ADMINS
# ------------------------------------------------

def list_admins(session):

    admins = session.exec(
        select(UserRole).where(UserRole.role == "admin")
    ).all()

    return admins
