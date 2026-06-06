# ==============================================================
# TRACE SERVICE
# ==============================================================

from sqlalchemy import text


# --------------------------------------------------------------
# TRACE DECISION
# --------------------------------------------------------------

def trace_decision(session, query):

    print(f"[DEBUG] Trace | query={query}")

    # ----------------------------------------------------------
    # FIND DECISION WITH LINEAGE
    # ----------------------------------------------------------

    decision = session.execute(
        text("""
            SELECT m.id, m.summary
            FROM memory m
            JOIN decision_lineage d
            ON m.id = d.decision_id
            WHERE m.memory_type = 'decision'
            AND m.summary ILIKE :query
            ORDER BY m.created_at DESC
            LIMIT 1
        """),
        {"query": f"%{query}%"}
    ).fetchone()

    if not decision:
        print("[DEBUG] Trace | no decision found")
        return "No reasoning trace found."

    decision_id = decision[0]
    decision_text = decision[1]

    print(f"[DEBUG] Trace | decision_id={decision_id}")

    # ----------------------------------------------------------
    # GET LINEAGE
    # ----------------------------------------------------------

    lineage = session.execute(
        text("""
            SELECT reasoning_engine,
                   triggered_by_user,
                   created_at
            FROM decision_lineage
            WHERE decision_id = :decision_id
        """),
        {"decision_id": decision_id}
    ).fetchone()

    # ----------------------------------------------------------
    # RELATED MEMORIES
    # ----------------------------------------------------------

    related = session.execute(
        text("""
            SELECT summary
            FROM memory
            WHERE memory_type IN ('task','event','insight')
            ORDER BY created_at DESC
            LIMIT 5
        """)
    ).fetchall()

    # ----------------------------------------------------------
    # FORMAT RESPONSE
    # ----------------------------------------------------------

    response = "Decision Trace\n\n"

    response += "Decision\n"
    response += f"• {decision_text}\n\n"

    if lineage:

        engine, user, created = lineage

        response += "Lineage\n"
        response += f"• Engine: {engine}\n"
        response += f"• Triggered by: {user}\n"
        response += f"• Created: {created}\n\n"

    if related:

        response += "Recent Related Memories\n"

        for r in related:
            response += f"• {r[0]}\n"

    return response