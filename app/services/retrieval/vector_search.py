from sqlalchemy import text

from app.services.memory.scope import (
    MemoryIdentityScope,
    legacy_chat_scope,
    raw_identity_predicate,
)


def vector_search_for_scope(
    session,
    embedding,
    scope: MemoryIdentityScope,
    limit: int = 5,
):
    """
    Perform vector retrieval inside one explicit workspace/identity scope.
    """
    if embedding is None:
        print(
            "VECTOR SEARCH SKIPPED: no embedding"
        )
        return []

    embedding_param = (
        embedding.tolist()
        if hasattr(
            embedding,
            "tolist",
        )
        else embedding
    )

    (
        identity_predicate,
        identity_params,
    ) = raw_identity_predicate(
        scope
    )

    statement = text(
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
        ORDER BY
            embedding
            <=> CAST(:embedding AS vector)
        LIMIT :limit
        """
    )

    params = {
        "embedding":
            embedding_param,
        "workspace_id":
            scope.workspace_id,
        "limit":
            limit,
        **identity_params,
    }

    results = session.execute(
        statement,
        params,
    )

    return results.fetchall()


def vector_search(
    session,
    embedding,
    chat_id,
    workspace_id: str,
    limit: int = 5,
):
    """
    Preserve the established legacy chat-scoped retrieval API.
    """
    return vector_search_for_scope(
        session=session,
        embedding=embedding,
        scope=legacy_chat_scope(
            workspace_id,
            chat_id,
        ),
        limit=limit,
    )
