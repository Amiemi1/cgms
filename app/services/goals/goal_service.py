# ==============================================================
# GOAL SERVICE
# ==============================================================

from asyncio import tasks

from sqlmodel import select
from sqlalchemy import text
from app.db.models.memory import Memory
from app.services.context.context_service import get_context
from app.services.metacognition.reflection_service import get_goal_reflections


# --------------------------------------------------------------
# CREATE GOAL
# --------------------------------------------------------------

def create_goal(session, chat_id, title, description=None):

    query = text("""
        INSERT INTO goal (chat_id, title, description)
        VALUES (:chat_id, :title, :description)
        RETURNING id
    """)

    result = session.execute(
        query,
        {
            "chat_id": chat_id,
            "title": title,
            "description": description
        }
    )

    goal_id = result.fetchone()[0]

    session.commit()

    return goal_id


# --------------------------------------------------------------
# LIST GOALS
# --------------------------------------------------------------

def list_goals(session, chat_id):

    query = text("""
        SELECT id, title, status, created_at
        FROM goal
        WHERE chat_id = :chat_id
        AND status = 'active'
        ORDER BY created_at DESC
    """)

    results = session.execute(
        query,
        {"chat_id": chat_id}
    ).fetchall()

    return results


# --------------------------------------------------------------
# GET GOAL
# --------------------------------------------------------------

def get_goal(session, goal_id):

    query = text("""
        SELECT id, title, description, status
        FROM goal
        WHERE id = :goal_id
    """)

    result = session.execute(
        query,
        {"goal_id": goal_id}
    ).fetchone()

    return result


# --------------------------------------------------------------
# STORE TASKS FOR GOAL
# --------------------------------------------------------------

def store_goal_tasks(session, chat_id, goal_id, tasks):

    stored = []

    for task in tasks:

        query = text("""
            INSERT INTO memory
            (
                chat_id,
                summary,
                memory_type,
                status,
                priority,
                importance,
                reminder_sent,
                goal_id,
                created_at
            )
            VALUES
            (
                :chat_id,
                :summary,
                'task',
                'active',
                50,
                1,
                FALSE,
                :goal_id,
                NOW()
            )
            RETURNING id
        """)

        result = session.execute(
            query,
            {
                "chat_id": chat_id,
                "summary": task,
                "goal_id": goal_id
            }
        )

        task_id = result.fetchone()[0]
        stored.append(task_id)

    session.commit()

    return stored


# --------------------------------------------------------------
# GENERATE GOAL PLAN
# --------------------------------------------------------------

def generate_goal_plan(session, chat_id, goal_text):

    context = get_context(session, chat_id)

    q = goal_text.lower()

    # ----------------------------------------------------------
    # CONTEXT-AWARE PLANNING
    # ----------------------------------------------------------

    if context:
        q = f"{context} {q}"

    # ----------------------------------------------------------
    # DISTRIBUTOR MEETING PLAN
    # ----------------------------------------------------------

    if "meeting" in q and "distributor" in q:

        tasks = [
            "Prepare slides",
            "Review distributor performance",
            "Confirm meeting venue",
            "Prepare talking points"
        ]

    # ----------------------------------------------------------
    # GENERIC MEETING PLAN
    # ----------------------------------------------------------

    elif "meeting" in q:

        tasks = [
            "Prepare agenda",
            "Review relevant data",
            "Confirm attendees",
            "Prepare talking points"
        ]

    # ----------------------------------------------------------
    # DEFAULT PLAN
    # ----------------------------------------------------------

    else:

        tasks = [
            f"Define plan for: {goal_text}",
            "Break goal into tasks",
            "Execute tasks",
            "Review results"
        ]

    # ----------------------------------------------------------
    # APPLY LEARNING FROM REFLECTIONS
    # ----------------------------------------------------------

    reflections = get_goal_reflections(session, chat_id)

    print("[DEBUG] Goal Planner | Retrieved reflections:", reflections)

    for r in reflections:

        r_lower = r.lower()

        if "smaller tasks" in r_lower:

            print("[DEBUG] Goal Planner | Applying learning: smaller tasks")

            tasks.insert(0, "Break preparation into smaller tasks")

        if "data" in r_lower or "analysis" in r_lower:

            print("[DEBUG] Goal Planner | Applying learning: data analysis")

            tasks.append("Prepare distributor sales analysis")

        return tasks

# --------------------------------------------------------------
# CHECK GOAL COMPLETION
# --------------------------------------------------------------

from sqlalchemy import text


def check_goal_completion(session, goal_id):

    total_query = text("""
        SELECT COUNT(*)
        FROM memory
        WHERE goal_id = :goal_id
        AND memory_type = 'task'
    """)

    completed_query = text("""
        SELECT COUNT(*)
        FROM memory
        WHERE goal_id = :goal_id
        AND memory_type = 'task'
        AND status = 'completed'
    """)

    total = session.execute(total_query, {"goal_id": goal_id}).scalar()
    completed = session.execute(completed_query, {"goal_id": goal_id}).scalar()

    if total == 0:
        return False

    return completed == total