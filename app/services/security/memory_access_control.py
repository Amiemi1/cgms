from sqlmodel import select
from app.db.models.memory import Memory
from app.db.models.memory_access import MemoryAccess
from app.services.workspace.tenant_scope import (
    inherit_workspace_id,
    load_scoped_record,
    normalize_workspace_id,
)


def grant_access(
    session,
    memory_id: int,
    user_id: int,
    permission: str,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    memory = load_scoped_record(
        session,
        Memory,
        memory_id,
        resolved_workspace_id,
    )

    if memory is None:
        return False

    access = MemoryAccess(
        workspace_id=inherit_workspace_id(memory),
        memory_id=memory_id,
        user_id=user_id,
        permission=permission
    )

    session.add(access)
    session.commit()

    return True


def revoke_access(
    session,
    memory_id: int,
    user_id: int,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    access = session.exec(
        select(MemoryAccess).where(
            MemoryAccess.workspace_id == resolved_workspace_id,
            MemoryAccess.memory_id == memory_id,
            MemoryAccess.user_id == user_id
        )
    ).first()

    if access:
        session.delete(access)
        session.commit()


def check_access(
    session,
    memory_id: int,
    user_id: int,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    access = session.exec(
        select(MemoryAccess).where(
            MemoryAccess.workspace_id == resolved_workspace_id,
            MemoryAccess.memory_id == memory_id,
            MemoryAccess.user_id == user_id
        )
    ).first()

    return access
