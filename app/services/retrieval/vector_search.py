from sqlalchemy import text


def vector_search(session, embedding, chat_id, limit=5):

    if embedding is None:
        print("VECTOR SEARCH SKIPPED: no embedding")
        return []

    embedding_param = embedding.tolist() if hasattr(embedding, "tolist") else embedding

    statement = text("""
        SELECT
            id,
            summary,
            memory_type,
            1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM memory
        WHERE chat_id = :chat_id
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    params = {
        "embedding": embedding_param,
        "chat_id": chat_id,
        "limit": limit
    }

    results = session.execute(statement, params)

    return results.fetchall()