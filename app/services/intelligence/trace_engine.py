# ==============================================================
# TRACE ENGINE
# ==============================================================

from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship
from app.services.retrieval.embedding_service import generate_embedding
from app.services.retrieval.vector_search import vector_search


def trace_reasoning(session, chat_id, query):

    # ------------------------------------------------
    # Find closest memory
    # ------------------------------------------------

    embedding = generate_embedding(query)

    results = vector_search(
        session=session,
        embedding=embedding,
        chat_id=chat_id,
        limit=1
    )

    if not results:
        return "No reasoning trace found."

    start_memory_id = results[0][0]

    start_memory = session.get(Memory, start_memory_id)

    if not start_memory:
        return "No reasoning trace found."

    trace = [start_memory.summary]

    current_id = start_memory_id

    # ------------------------------------------------
    # Follow reasoning chain
    # ------------------------------------------------

    for _ in range(5):

        relation = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.source_memory_id == current_id
            )
        ).first()

        if not relation:
            break

        next_memory = session.get(Memory, relation.target_memory_id)

        if not next_memory:
            break

        trace.append(next_memory.summary)

        current_id = next_memory.id

    # ------------------------------------------------
    # Format output
    # ------------------------------------------------

    response = "🧠 Reasoning Trace\n\n"

    for i, step in enumerate(trace):

        response += step

        if i < len(trace) - 1:
            response += "\n   ↓\n"

    return response