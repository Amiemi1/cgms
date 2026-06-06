# ==============================================================
# CONTEXT SERVICE
# ==============================================================

from sqlalchemy import text


def set_context(session, chat_id, context):

    query = text("""
        INSERT INTO context_state (chat_id, context)
        VALUES (:chat_id, :context)
    """)

    session.execute(query, {
        "chat_id": chat_id,
        "context": context
    })

    session.commit()


def get_context(session, chat_id):

    query = text("""
        SELECT context
        FROM context_state
        WHERE chat_id = :chat_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    result = session.execute(
        query,
        {"chat_id": chat_id}
    ).fetchone()

    if result:
        return result[0]

    return None


def clear_context(session, chat_id):

    query = text("""
        DELETE FROM context_state
        WHERE chat_id = :chat_id
    """)

    session.execute(query, {"chat_id": chat_id})

    session.commit()