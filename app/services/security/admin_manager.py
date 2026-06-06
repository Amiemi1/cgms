from sqlmodel import select
from app.db.models.security_models import UserRole


# ------------------------------------------------
# ADD ADMIN
# ------------------------------------------------

def add_admin(session, user_id: int):

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
    session.commit()

    return True


# ------------------------------------------------
# REMOVE ADMIN
# ------------------------------------------------

def remove_admin(session, user_id: int):

    role = session.exec(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role == "admin"
        )
    ).first()

    if not role:
        return False

    session.delete(role)
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