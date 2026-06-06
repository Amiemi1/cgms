# ==============================================================
# AUTONOMOUS PRIORITY ENGINE
# ==============================================================

from sqlmodel import select
from collections import defaultdict

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def compute_strategic_score(memory, relationship_count):

    score = 0

    # AI importance score
    score += memory.importance * 2

    # user priority signal
    if memory.priority:
        score += memory.priority / 10

    # cluster strength
    score += memory.cluster_count

    # graph connectivity
    score += relationship_count

    return score


def generate_priorities(session, chat_id):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    relationship_map = defaultdict(int)

    for r in relationships:

        relationship_map[r.source_memory_id] += 1
        relationship_map[r.target_memory_id] += 1

    scored = []

    for m in memories:

        rel_count = relationship_map.get(m.id, 0)

        score = compute_strategic_score(m, rel_count)

        scored.append({
            "summary": m.summary,
            "type": m.memory_type,
            "score": score
        })

    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    return scored[:5]