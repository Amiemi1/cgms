# ==============================================================
# GOAL PROGRESS SERVICE
# ==============================================================

from sqlalchemy import text


def get_goal_progress(session, goal_id):

    # total tasks
    total_query = text("""
        SELECT COUNT(*)
        FROM memory
        WHERE goal_id = :goal_id
        AND memory_type = 'task'
    """)

    total = session.execute(
        total_query,
        {"goal_id": goal_id}
    ).scalar()


    # completed tasks
    completed_query = text("""
        SELECT COUNT(*)
        FROM memory
        WHERE goal_id = :goal_id
        AND memory_type = 'task'
        AND status = 'completed'
    """)

    completed = session.execute(
        completed_query,
        {"goal_id": goal_id}
    ).scalar()


    if total == 0:
        return None


    progress_percent = int((completed / total) * 100)

    return {
        "total": total,
        "completed": completed,
        "progress": progress_percent
    }