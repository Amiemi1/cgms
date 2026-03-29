from sqlmodel import Session, select

from app.db.models.memory_relationship import MemoryRelationship


def link_memories(
    session: Session,
    source_id: int,
    target_id: int,
    relationship_type: str
):

    relation = MemoryRelationship(
        source_memory_id=source_id,
        target_memory_id=target_id,
        relationship_type=relationship_type
    )

    session.add(relation)
    session.commit()

    return relation


def get_related_memories(session: Session, memory_id: int):

    relations = session.exec(
        select(MemoryRelationship).where(
            MemoryRelationship.source_memory_id == memory_id
        )
    ).all()

    return relations