# ==============================================================
# TASK EXECUTION SERVICE
# ==============================================================

from sqlalchemy import text


# --------------------------------------------------------------
# CREATE TASK DEPENDENCY
# --------------------------------------------------------------

def create_dependency(session, parent_task_id, child_task_id):

    query = text("""
        INSERT INTO task_dependency (parent_task_id, child_task_id)
        VALUES (:parent, :child)
    """)

    session.execute(
        query,
        {
            "parent": parent_task_id,
            "child": child_task_id
        }
    )

    session.commit()


# --------------------------------------------------------------
# GET NEXT AVAILABLE TASK
# --------------------------------------------------------------

def get_next_task(session, goal_id):

    query = text("""
        SELECT m.id, m.summary
        FROM memory m
        WHERE m.goal_id = :goal_id
        AND m.memory_type = 'task'
        AND m.status = 'active'
        AND NOT EXISTS (
            SELECT 1
            FROM task_dependency d
            JOIN memory parent
            ON parent.id = d.parent_task_id
            WHERE d.child_task_id = m.id
            AND parent.status != 'completed'
        )
        ORDER BY m.created_at ASC
        LIMIT 1
    """)

    result = session.execute(
        query,
        {"goal_id": goal_id}
    ).fetchone()

    return result


# --------------------------------------------------------------
# COMPLETE TASK
# --------------------------------------------------------------

def complete_task(session, task_id):

    update_query = text("""
        UPDATE memory
        SET status = 'completed'
        WHERE id = :task_id
    """)

    session.execute(update_query, {"task_id": task_id})
    session.commit()

    # ----------------------------------------------------------
    # GET GOAL INFORMATION
    # ----------------------------------------------------------

    goal_query = text("""
        SELECT goal_id, chat_id
        FROM memory
        WHERE id = :task_id
    """)

    result = session.execute(goal_query, {"task_id": task_id}).fetchone()

    if not result:
        return

    goal_id = result[0]
    chat_id = result[1]

    # ----------------------------------------------------------
    # CHECK IF GOAL IS COMPLETE
    # ----------------------------------------------------------

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
        return

    # ----------------------------------------------------------
    # AUTOMATIC REFLECTION TRIGGER
    # ----------------------------------------------------------

    print("DEBUG total:", total)
    print("DEBUG completed:", completed)

    if completed == total:

        print("Reflection condition reached")

        from app.services.metacognition.reflection_service import (
            generate_goal_reflection,
            record_reflection
        )

        observation, improvement = generate_goal_reflection(session, goal_id)

        print("Reflection generated:", observation, improvement)

        record_reflection(
            session,
            chat_id,
            goal_id,
            "automatic_goal_reflection",
            observation,
            improvement
        )

    print("Automatic reflection recorded for goal:", goal_id)