# =====================================================
# VECTOR MEMORY SEARCH SERVICE
# =====================================================

from sqlmodel import Session
from sqlalchemy import text

from app.services.workspace.tenant_scope import normalize_workspace_id


def search_memories(
    session,
    chat_id,
    embedding,
    workspace_id: str,
    limit=5,
):
    """
    Perform semantic search on memories using pgvector.
    """

    resolved_workspace_id = normalize_workspace_id(workspace_id)

    # -------------------------------------------------
    # DEBUG
    # -------------------------------------------------

    print(f"[DEBUG] Embedding length passed to search: {len(embedding)}")

    # -------------------------------------------------
    # VECTOR SEARCH QUERY
    # -------------------------------------------------

    query = text("""
        SELECT
            id,
            summary,
            memory_type,
            (embedding <-> CAST(:embedding AS vector)) AS distance
        FROM memory
        WHERE workspace_id = :workspace_id
          AND chat_id = :chat_id
          AND embedding IS NOT NULL
        ORDER BY embedding <-> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    # -------------------------------------------------
    # EXECUTE
    # -------------------------------------------------

    result = session.execute(
        query,
        {
            "embedding": embedding,
            "workspace_id": resolved_workspace_id,
            "chat_id": chat_id,
            "limit": limit
        }
    )

    rows = result.fetchall()

    # -------------------------------------------------
    # DEBUG RESULT
    # -------------------------------------------------

    print(f"[DEBUG] Vector search rows returned: {len(rows)}")

    return rows


# =====================================================
# SEMANTIC SEARCH SERVICE
# =====================================================


def search_memories(
    session: Session,
    chat_id: int,
    embedding: list,
    workspace_id: str,
    limit: int = 10,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    # Convert embedding list → pgvector string
    emb_str = "[" + ",".join([str(x) for x in embedding]) + "]"

    query = text("""
        SELECT id, summary, memory_type,
               1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM memory
        WHERE workspace_id = :workspace_id
          AND chat_id = :chat_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    rows = session.execute(query, {
        "embedding": emb_str,
        "workspace_id": resolved_workspace_id,
        "chat_id": chat_id,
        "limit": limit
    }).fetchall()

    return [
        {
            "id": r[0],
            "summary": r[1],
            "type": r[2],
            "score": float(r[3])
        }
        for r in rows
    ]
