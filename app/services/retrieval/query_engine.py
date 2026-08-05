from app.services.retrieval.vector_search import vector_search
from app.services.retrieval.embedding_service import generate_embedding
from app.services.workspace.tenant_scope import normalize_workspace_id


def run_query(
    session,
    chat_id: int,
    query: str,
    workspace_id: str,
    limit: int = 5,
):

    try:

        print("\nRETRIEVAL QUERY:", query)

        # --------------------------------
        # Generate embedding for question
        # --------------------------------

        embedding = generate_embedding(query)

        if embedding is None:
            print("Embedding generation failed")
            return []

        # --------------------------------
        # Perform vector search
        # --------------------------------

        results = vector_search(
            session=session,
            embedding=embedding,
            chat_id=chat_id,
            workspace_id=normalize_workspace_id(
                workspace_id
            ),
            limit=limit
        )

        memories = []

        for row in results:

            # row format:
            # (id, summary, memory_type, score)

            memories.append({
                "id": row[0],
                "summary": row[1],
                "type": row[2],
                "score": float(row[3])
            })

        print("RETRIEVAL RESULTS:", memories)

        return memories

    except Exception:

        import traceback
        print("\nRETRIEVAL ERROR")
        traceback.print_exc()

        return []
