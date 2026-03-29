from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory_relationship import MemoryRelationship

router = APIRouter(prefix="/memory-graph", tags=["Memory Graph"])


@router.get("/{memory_id}")
def get_relationships(memory_id: int):

    session = SessionLocal()

    try:

        relations = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.source_memory_id == memory_id
            )
        ).all()

        return relations

    finally:
        session.close()