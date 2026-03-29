from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory

router = APIRouter(prefix="/memory", tags=["Memory Actions"])


# ------------------------------
# COMPLETE TASK
# ------------------------------

@router.patch("/{memory_id}/complete")
def complete_memory(memory_id: int):

    session = SessionLocal()

    try:

        memory = session.get(Memory, memory_id)

        if not memory:
            return {"error": "Memory not found"}

        memory.status = "completed"

        session.add(memory)
        session.commit()

        return {"message": "Memory marked as completed"}

    finally:
        session.close()


# ------------------------------
# DELAY REMINDER
# ------------------------------

@router.patch("/{memory_id}/delay")
def delay_memory(memory_id: int, minutes: int = 60):

    from datetime import timedelta

    session = SessionLocal()

    try:

        memory = session.get(Memory, memory_id)

        if not memory:
            return {"error": "Memory not found"}

        if not memory.reminder_time:
            return {"error": "No reminder set"}

        memory.reminder_time = memory.reminder_time + timedelta(minutes=minutes)

        session.add(memory)
        session.commit()

        return {"message": "Reminder delayed"}

    finally:
        session.close()


# ------------------------------
# CHANGE PRIORITY
# ------------------------------

@router.patch("/{memory_id}/priority")
def update_priority(memory_id: int, priority: int):

    session = SessionLocal()

    try:

        memory = session.get(Memory, memory_id)

        if not memory:
            return {"error": "Memory not found"}

        memory.priority = priority

        session.add(memory)
        session.commit()

        return {"message": "Priority updated"}

    finally:
        session.close()


# ------------------------------
# DELETE MEMORY
# ------------------------------

@router.delete("/{memory_id}")
def delete_memory(memory_id: int):

    session = SessionLocal()

    try:

        memory = session.get(Memory, memory_id)

        if not memory:
            return {"error": "Memory not found"}

        session.delete(memory)
        session.commit()

        return {"message": "Memory deleted"}

    finally:
        session.close()