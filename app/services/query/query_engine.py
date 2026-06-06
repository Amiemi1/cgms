from app.db.session import SessionLocal

from app.services.retrieval.query_engine import run_query

from openai import OpenAI
from app.core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def answer_query(chat_id: int, question: str):

    session = SessionLocal()

    try:

        print("\nQUESTION:", question)

        # --------------------------------
        # Retrieve relevant memories
        # --------------------------------

        results = run_query(
            session=session,
            chat_id=chat_id,
            query=question,
            limit=5
        )

        print("RETRIEVAL RESULTS:", results)

        if not results:
            return "I could not find any relevant memories."

        # --------------------------------
        # Build context
        # --------------------------------

        context_memories = []

        for r in results:

            # results format:
            # {'id': 25, 'summary': 'text', 'type': 'task', 'score': 0.72}

            context_memories.append(r["summary"])

        context_text = "\n".join(context_memories)

        print("\nCONTEXT:")
        print(context_text)

        # --------------------------------
        # Build prompt
        # --------------------------------

        prompt = f"""
You are an assistant analyzing a user's memory system.

Memories:
{context_text}

Question:
{question}

Answer clearly using the memories.
"""

        # --------------------------------
        # Ask OpenAI
        # --------------------------------

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You analyze user memories."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content

        print("\nAI RESPONSE:", answer)

        return answer

    except Exception:

        import traceback

        print("\nQUERY ENGINE ERROR")
        traceback.print_exc()

        return "Error processing query."

    finally:

        session.close()