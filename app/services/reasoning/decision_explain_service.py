# ==============================================================
# DECISION EXPLAIN SERVICE
# ==============================================================

from sqlalchemy import text


# --------------------------------------------------------------
# EXPLAIN DECISION
# --------------------------------------------------------------

def explain_decision(session, query):

    print(f"[DEBUG] Explain Service | query={query}")

    # ----------------------------------------------------------
    # FIND DECISION THAT HAS LINEAGE
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
        print("[DEBUG] Explain | No decision found with lineage")
        return "No explanation available."

    decision_id = decision[0]
    decision_text = decision[1]

    print(f"[DEBUG] Explain | decision_id={decision_id}")

    # ----------------------------------------------------------
    # FETCH LINEAGE
    # ----------------------------------------------------------

    lineage = session.execute(
        text("""
            SELECT reasoning_engine,
                   triggered_by_user,
                   created_at
            FROM decision_lineage
            WHERE decision_id = :decision_id
            LIMIT 1
        """),
        {"decision_id": decision_id}
    ).fetchone()

    if not lineage:
        print("[DEBUG] Explain | lineage missing")
        return "Decision found but no lineage recorded."

    reasoning_engine, user_id, created_at = lineage

    print("[DEBUG] Explain | lineage retrieved")

    # ----------------------------------------------------------
    # FORMAT RESPONSE
    # ----------------------------------------------------------

    response = "Decision\n"
    response += f"• {decision_text}\n\n"

    response += "Decision Metadata\n"
    response += f"• Reasoning Engine: {reasoning_engine}\n"
    response += f"• Triggered by user: {user_id}\n"
    response += f"• Created: {created_at}\n"

    return response