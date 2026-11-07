from sqlalchemy import text
from sqlmodel import Session

from app.services.memory.scope import (
    MemoryIdentityScope,
    legacy_chat_scope,
    raw_identity_predicate,
)


def search_memories_for_scope(
    session: Session,
    embedding: list,
    scope: MemoryIdentityScope,
    limit: int = 10,
):
    """
    Perform semantic memory search in one explicit identity scope.
    """
    emb_str = (
        "["
        + ",".join(
            str(value)
            for value in embedding
        )
        + "]"
    )

    (
        identity_predicate,
        identity_params,
    ) = raw_identity_predicate(
        scope
    )

    query = text(
        """
        SELECT
            id,
            summary,
            memory_type,
            1 - (
                embedding
                <=> CAST(:embedding AS vector)
            ) AS score
        FROM memory
        WHERE workspace_id = :workspace_id
          AND """
        + identity_predicate
        + """
          AND embedding IS NOT NULL
        ORDER BY
            embedding
            <=> CAST(:embedding AS vector)
        LIMIT :limit
        """
    )

    params = {
        "embedding":
            emb_str,
        "workspace_id":
            scope.workspace_id,
        "limit":
            limit,
        **identity_params,
    }

    rows = session.execute(
        query,
        params,
    ).fetchall()

    return [
        {
            "id": row[0],
            "summary": row[1],
            "type": row[2],
            "score": float(
                row[3]
            ),
        }
        for row in rows
    ]


def search_memories(
    session: Session,
    chat_id: int,
    embedding: list,
    workspace_id: str,
    limit: int = 10,
):
    """
    Preserve the established legacy chat-scoped semantic-search API.
    """
    return search_memories_for_scope(
        session=session,
        embedding=embedding,
        scope=legacy_chat_scope(
            workspace_id,
            chat_id,
        ),
        limit=limit,
    )
