from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.user import User


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# --------------------------------------------------
# Utility
# --------------------------------------------------

def get_user_chat(session, user_id: int):

    user = session.get(User, user_id)

    if not user or not user.chat_id:
        return None

    return user.chat_id


def memory_to_dict(m: Memory):

    return {
        "id": m.id,
        "summary": m.summary,
        "priority": m.priority,
        "type": m.memory_type,
        "status": m.status,
        "created_at": m.created_at,
        "reminder_time": m.reminder_time
    }


# --------------------------------------------------
# TASKS PANEL
# --------------------------------------------------

@router.get("/tasks/{user_id}")
def get_tasks(user_id: int):

    session = SessionLocal()

    try:

        chat_id = get_user_chat(session, user_id)

        if not chat_id:
            return []

        tasks = session.exec(
            select(Memory)
            .where(
                Memory.chat_id == chat_id,
                Memory.memory_type == "task",
                Memory.status == "active"
            )
            .order_by(Memory.priority)
        ).all()

        return [memory_to_dict(m) for m in tasks]

    finally:
        session.close()


# --------------------------------------------------
# EVENTS PANEL
# --------------------------------------------------

@router.get("/events/{user_id}")
def get_events(user_id: int):

    session = SessionLocal()

    try:

        chat_id = get_user_chat(session, user_id)

        if not chat_id:
            return []

        events = session.exec(
            select(Memory)
            .where(
                Memory.chat_id == chat_id,
                Memory.memory_type == "event"
            )
            .order_by(Memory.reminder_time)
        ).all()

        return [memory_to_dict(m) for m in events]

    finally:
        session.close()


# --------------------------------------------------
# DECISIONS PANEL
# --------------------------------------------------

@router.get("/decisions/{user_id}")
def get_decisions(user_id: int):

    session = SessionLocal()

    try:

        chat_id = get_user_chat(session, user_id)

        if not chat_id:
            return []

        decisions = session.exec(
            select(Memory)
            .where(
                Memory.chat_id == chat_id,
                Memory.memory_type == "decision"
            )
            .order_by(Memory.created_at.desc())
        ).all()

        return [memory_to_dict(m) for m in decisions]

    finally:
        session.close()


# --------------------------------------------------
# INSIGHTS PANEL
# --------------------------------------------------

@router.get("/insights/{user_id}")
def get_insights(user_id: int):

    session = SessionLocal()

    try:

        chat_id = get_user_chat(session, user_id)

        if not chat_id:
            return []

        memories = session.exec(
            select(Memory)
            .where(Memory.chat_id == chat_id)
            .order_by(Memory.priority)
            .limit(20)
        ).all()

        insights = []

        for m in memories:

            if m.priority <= 20:
                insights.append({
                    "type": "high_priority",
                    "message": f"High priority item: {m.summary}"
                })

            if m.reminder_time:
                insights.append({
                    "type": "upcoming_event",
                    "message": f"Upcoming reminder: {m.summary}",
                    "time": m.reminder_time
                })

        return insights

    finally:
        session.close()


# --------------------------------------------------
# MEMORY TIMELINE
# --------------------------------------------------

@router.get("/timeline/{user_id}")
def get_timeline(user_id: int):

    session = SessionLocal()

    try:

        chat_id = get_user_chat(session, user_id)

        if not chat_id:
            return []

        memories = session.exec(
            select(Memory)
            .where(Memory.chat_id == chat_id)
            .order_by(Memory.created_at.desc())
        ).all()

        return [
            {
                "time": m.created_at,
                "type": m.memory_type,
                "summary": m.summary
            }
            for m in memories
        ]

    finally:
        session.close()