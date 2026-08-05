from sqlalchemy import text

from app.services.workspace.tenant_scope import normalize_workspace_id


def vector_search(
    session,
    embedding,
    chat_id,
    workspace_id: str,
    limit=5,
):

    if embedding is None:
        print("VECTOR SEARCH SKIPPED: no embedding")
        return []

    resolved_workspace_id = normalize_workspace_id(workspace_id)
    embedding_param = (
        embedding.tolist()
        if hasattr(embedding, "tolist")
        else embedding
    )

    statement = text("""
        SELECT
            id,
            summary,
            memory_type,
            1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM memory
        WHERE workspace_id = :workspace_id
          AND chat_id = :chat_id
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    params = {
        "embedding": embedding_param,
        "workspace_id": resolved_workspace_id,
        "chat_id": chat_id,
        "limit": limit
    }

    results = session.execute(statement, params)

    return results.fetchall()
