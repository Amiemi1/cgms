# ==============================================================
# GOVERNANCE AUDIT SERVICE
# ==============================================================

from sqlalchemy import text


def record_audit(session, user_id, action, details):

    print(f"[DEBUG] Governance | Audit record | user={user_id} action={action}")

    session.execute(
        text("""
            INSERT INTO governance_audit (user_id, action, details)
            VALUES (:user_id, :action, :details)
        """),
        {
            "user_id": user_id,
            "action": action,
            "details": details
        }
    )

    session.commit()


def get_recent_audit(session, limit=10):

    result = session.execute(
        text("""
            SELECT user_id, action, details, created_at
            FROM governance_audit
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    ).fetchall()

    return result