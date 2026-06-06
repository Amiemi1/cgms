# =====================================================
# AGENT ORCHESTRATOR
# Coordinates planning and optional execution
# =====================================================

from app.services.agent.planner import generate_plan
from app.services.agent.action_engine import execute_plan
from app.services.agent.learning_engine import record_action


def run_agent(session, chat_id: int, goal: str, execute=False):

    print("AGENT RUNNING FOR GOAL:", goal)

    plan = generate_plan(session, chat_id, goal)

    if not plan:
        return "No plan could be generated."

    # --------------------------------
    # Execution optional
    # --------------------------------
    created_tasks = []

    if execute:

        created_tasks = execute_plan(session, chat_id, plan)

        record_action(
            session,
            action="execute_plan",
            context=goal,
            result="success"
        )

    # --------------------------------
    # Build response
    # --------------------------------
    response = "Generated plan:\n\n"

    for step in plan:
        response += f"• {step}\n"

    if execute:
        response += "\nTasks created."

    return response