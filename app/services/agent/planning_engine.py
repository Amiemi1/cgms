# =====================================================
# PLANNING ENGINE
# Generates structured plans from conversational goals
# =====================================================

from sqlmodel import select

from app.db.models.memory import Memory
from app.services.agent.goal_context_engine import build_goal_context


def generate_plan(session, chat_id: int, goal: str):

    print("PLANNING ENGINE RUNNING FOR GOAL:", goal)

    goal = goal.lower()

    # ------------------------------------------------
    # STEP 1 — Build goal context using graph expansion
    # ------------------------------------------------

    context = build_goal_context(session, chat_id, goal)

    # ------------------------------------------------
    # STEP 2 — Extract tasks from context
    # ------------------------------------------------

    steps = []

    for memory in context:

        if memory.memory_type == "task":

            steps.append(memory.summary)

    # ------------------------------------------------
    # STEP 3 — Fallback if no context tasks found
    # ------------------------------------------------

    if not steps:

        memories = session.exec(
            select(Memory).where(
                Memory.chat_id == chat_id,
                Memory.memory_type == "task"
            )
        ).all()

        for m in memories:

            if any(word in m.summary.lower() for word in goal.split()):

                steps.append(m.summary)

    # ------------------------------------------------
    # STEP 4 — If still nothing, create placeholder
    # ------------------------------------------------

    if not steps:

        steps.append("Define tasks required to achieve this goal")

    # ------------------------------------------------
    # STEP 5 — Remove duplicates
    # ------------------------------------------------

    unique_steps = list(dict.fromkeys(steps))

    # ------------------------------------------------
    # STEP 6 — Return structured plan
    # ------------------------------------------------

    plan = []

    for i, step in enumerate(unique_steps, 1):

        plan.append(step)

    print("PLAN GENERATED:", plan)

    return plan