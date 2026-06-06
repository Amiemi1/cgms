from sqlmodel import select
from app.db.models.memory_access import MemoryAccess


def grant_access(session, memory_id: int, user_id: int, permission: str):

    access = MemoryAccess(
        memory_id=memory_id,
        user_id=user_id,
        permission=permission
    )

    session.add(access)
    session.commit()

    return True


def revoke_access(session, memory_id: int, user_id: int):

    access = session.exec(
        select(MemoryAccess).where(
            MemoryAccess.memory_id == memory_id,
            MemoryAccess.user_id == user_id
        )
    ).first()

    if access:
        session.delete(access)
        session.commit()


def check_access(session, memory_id: int, user_id: int):

    access = session.exec(
        select(MemoryAccess).where(
            MemoryAccess.memory_id == memory_id,
            MemoryAccess.user_id == user_id
        )
    ).first()

    return access