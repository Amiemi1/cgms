# ==============================================================
# EXPLAINABILITY ENGINE
# ==============================================================

from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship

from app.services.retrieval.embedding_service import generate_embedding
from app.services.retrieval.vector_search import vector_search


def explain_memory(session, chat_id, query):

    # ------------------------------------------------
    # Generate embedding for query
    # ------------------------------------------------

    embedding = generate_embedding(query)

    # ------------------------------------------------
    # Find closest memory
    # ------------------------------------------------

    results = vector_search(
        session=session,
        embedding=embedding,
        chat_id=chat_id,
        limit=1
    )

    if not results:
        return "No explanation available."

    memory_id = results[0][0]

    target = session.get(Memory, memory_id)

    if not target:
        return "No explanation available."

    # ------------------------------------------------
    # Retrieve relationships
    # ------------------------------------------------

    relationships = session.exec(
        select(MemoryRelationship).where(
            MemoryRelationship.source_memory_id == target.id
        )
    ).all()

    # ------------------------------------------------
    # Build explanation
    # ------------------------------------------------

    response = f"🔎 Explanation for:\n{target.summary}\n\n"

    if relationships:

        response += "Reasoning chain:\n\n"

        for r in relationships:

            related_memory = session.get(Memory, r.target_memory_id)

            if not related_memory:
                continue

            if r.relationship_type == "triggered_by":

                response += (
                    "This task was created because of the event:\n"
                    f"• {related_memory.summary}\n\n"
                )

            elif r.relationship_type == "resolves":

                response += (
                    "This decision resolves the task:\n"
                    f"• {related_memory.summary}\n\n"
                )

            else:

                response += (
                    f"Relationship ({r.relationship_type}) with:\n"
                    f"• {related_memory.summary}\n\n"
                )

    else:

        response += "No graph relationships found.\n\n"

    response += "Memory type:\n"
    response += f"• {target.memory_type}"

    return response