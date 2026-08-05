from fastapi import APIRouter, Depends

from app.db.session import SessionLocal
from app.services.embedding.embedding_service import generate_embedding
from app.services.search.vector_search_service import search_memories
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import get_current_workspace_id


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



@router.get("/")
def search(
    query: str,
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        embedding = generate_embedding(query)

        results = search_memories(
            session=session,
            chat_id=chat_id,
            embedding=embedding,
            workspace_id=workspace_id,
            limit=5
        )

        return [
            {
                "id": r.id,
                "summary": r.summary,
                "type": r.memory_type
            }
            for r in results
        ]

    finally:
        session.close()
