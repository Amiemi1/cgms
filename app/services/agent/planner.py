from app.services.retrieval.query_engine import run_query


def generate_plan(session, chat_id: int, goal: str):

    print("PLANNER GOAL:", goal)

    results = run_query(session, chat_id, goal)

    if not results:
        return []

    tasks = []
    decisions = []
    events = []

    for r in results:

        if r["type"] == "task":
            tasks.append(r["summary"])

        elif r["type"] == "decision":
            decisions.append(r["summary"])

        elif r["type"] == "event":
            events.append(r["summary"])

    plan = []

    for t in tasks:
        plan.append(t)

    for d in decisions:
        plan.append(f"Confirm decision: {d}")

    for e in events:
        plan.append(f"Prepare for event: {e}")

    print("PLAN GENERATED:", plan)

    return plan