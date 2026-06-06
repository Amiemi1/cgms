from sqlmodel import Session, select
from app.db.models.security_models import UserRole


# ----------------------------------------------------------
# GET USER ROLE
# ----------------------------------------------------------

def get_user_role(session: Session, user_id: int):

    statement = select(UserRole).where(UserRole.user_id == user_id)
    result = session.exec(statement).first()

    if result:
        return result.role

    return "user"


# ----------------------------------------------------------
# CHECK ADMIN
# ----------------------------------------------------------

def is_admin(session: Session, user_id: int) -> bool:

    statement = select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role == "admin"
    )

    result = session.exec(statement).first()

    return result is not None


# ----------------------------------------------------------
# CHECK MEMORY CREATION PERMISSION
# ----------------------------------------------------------

def can_create_memory(session: Session, user_id: int) -> bool:

    role = get_user_role(session, user_id)

    if role in ["admin", "moderator", "user"]:
        return True

    return False