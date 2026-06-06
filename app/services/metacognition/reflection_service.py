# ==============================================================
# REFLECTION SERVICE
# ==============================================================

from sqlalchemy import text


def record_reflection(session, chat_id, goal_id, reflection_type, observation, improvement):

    query = text("""
        INSERT INTO cognitive_reflection
        (chat_id, goal_id, reflection_type, observation, improvement)
        VALUES (:chat_id, :goal_id, :reflection_type, :observation, :improvement)
    """)

    session.execute(
        query,
        {
            "chat_id": chat_id,
            "goal_id": goal_id,
            "reflection_type": reflection_type,
            "observation": observation,
            "improvement": improvement
        }
    )

    session.commit()

# --------------------------------------------------------------
# GENERATE REFLECTION
# --------------------------------------------------------------

def generate_goal_reflection(session, goal_id):

    query = text("""
        SELECT status
        FROM memory
        WHERE goal_id = :goal_id
        AND memory_type = 'task'
    """)

    tasks = session.execute(query, {"goal_id": goal_id}).fetchall()

    if not tasks:
        return None

    total = len(tasks)
    completed = sum(1 for t in tasks if t[0] == "completed")

    completion_rate = completed / total

    if completion_rate == 1:
        observation = "Goal completed successfully."
        improvement = "Current planning approach is effective."

    elif completion_rate > 0.5:
        observation = "Goal partially completed."
        improvement = "Review unfinished tasks and adjust planning."

    else:
        observation = "Goal execution struggled."
        improvement = "Break goal into smaller tasks."

    return observation, improvement


from sqlalchemy import text

# --------------------------------------------------------------
# RETRIEVE RELEVANT REFLECTIONS
# --------------------------------------------------------------

def get_goal_reflections(session, chat_id):

    query = text("""
        SELECT improvement
        FROM cognitive_reflection
        WHERE chat_id = :chat_id
        ORDER BY created_at DESC
        LIMIT 5
    """)

    rows = session.execute(query, {"chat_id": chat_id}).fetchall()

    return [r[0] for r in rows]