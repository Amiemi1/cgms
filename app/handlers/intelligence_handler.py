# =============================================================
# INTELLIGENCE HANDLERS
# =============================================================

from aiogram import F
from aiogram.types import Message

from sqlalchemy import text

from app.db.session import SessionLocal

from app.services.intelligence.intelligence_engine import generate_intelligence_report
from app.services.intelligence.priority_engine import generate_priorities
from app.services.strategy.strategy_engine import generate_strategy

from app.services.search.vector_search_service import search_memories
from app.services.embedding.embedding_service import generate_embedding
from app.services.workspace.tenant_scope import resolve_legacy_workspace_id


def register_intelligence_handlers(dp):

    # =========================================================
    # INTELLIGENCE REPORT
    # =========================================================

    @dp.message(F.text == "/intelligence")
    async def intelligence_handler(message: Message):

        session = SessionLocal()

        try:

            report = generate_intelligence_report(
                session,
                message.chat.id
            )

            await message.answer(report)

        finally:
            session.close()

    # =========================================================
    # PRIORITIES
    # =========================================================

    @dp.message(F.text == "/priorities")
    async def priorities_handler(message: Message):

        session = SessionLocal()

        try:

            priorities = generate_priorities(
                session,
                message.chat.id
            )

            if not priorities:
                await message.answer("No priorities found.")
                return

            response = "🔥 Top Priorities\n\n"

            for i, p in enumerate(priorities, start=1):
                response += f"{i}. {p['summary']}\n"

            await message.answer(response)

        finally:
            session.close()

    # =========================================================
    # STRATEGY
    # =========================================================

    @dp.message(F.text.startswith("/strategy"))
    async def strategy_handler(message: Message):

        session = SessionLocal()

        try:

            goal = message.text.replace("/strategy", "").strip()

            if not goal:
                await message.answer("Usage: /strategy <goal>")
                return

            strategy = generate_strategy(
                session=session,
                chat_id=message.chat.id,
                goal=goal
            )

            response = "📈 Strategy Recommendation\n\n"

            if isinstance(strategy, dict):

                focus = strategy.get("focus_topic", "Unknown")
                blocked = strategy.get("blocked_tasks", [])

                response += f"Strategic focus: {focus}\n\n"

                if blocked:
                    response += "Risks to address:\n"

                    for t in blocked:
                        response += f"• {t}\n"

            else:

                response += str(strategy)

            await message.answer(response)

        finally:
            session.close()

    # =========================================================
    # MEMORY BROWSER
    # =========================================================

    @dp.message(F.text == "/memory")
    async def memory_handler(message: Message):

        workspace_id = resolve_legacy_workspace_id()
        session = SessionLocal()

        try:

            result = session.execute(text("""
                SELECT id, summary, memory_type, is_locked
                FROM memory
                WHERE workspace_id = :workspace_id
                  AND chat_id = :chat_id
                ORDER BY created_at DESC
                LIMIT 10
            """), {
                "workspace_id": workspace_id,
                "chat_id": message.chat.id,
            })

            rows = result.fetchall()

            if not rows:
                await message.answer("No memories stored.")
                return

            response = "🧠 Recent Memories\n\n"

            for m in rows:

                lock_icon = " 🔒" if m.is_locked else ""
                response += f"[{m.id}] ({m.memory_type}) {m.summary}{lock_icon}\n"

            await message.answer(response)

        finally:
            session.close()

    # =========================================================
    # SEMANTIC SEARCH
    # =========================================================

    @dp.message(F.text.startswith("/search"))
    async def search_handler(message: Message):

        workspace_id = resolve_legacy_workspace_id()
        session = SessionLocal()

        try:

            query = message.text.replace("/search", "").strip()

            if not query:
                await message.answer("Usage: /search <query>")
                return

            print(f"[DEBUG] Search query: {query}")

            # ---------------------------------------------
            # Generate embedding
            # ---------------------------------------------

            query_embedding = generate_embedding(query)

            # ---------------------------------------------
            # Vector search
            # ---------------------------------------------

            results = search_memories(
                session=session,
                chat_id=message.chat.id,
                embedding=query_embedding,
                workspace_id=workspace_id,
                limit=5
            )

            print(f"[DEBUG] Results returned: {len(results)}")

            if not results:
                await message.answer("No relevant memories found.")
                return

            response = "🔎 Memory Search Results\n\n"

            for r in results:

                icon = "📝"

                if r.memory_type == "decision":
                    icon = "⚖️"

                elif r.memory_type == "event":
                    icon = "📅"

                elif r.memory_type == "task":
                    icon = "✅"

                response += f"{icon} [{r.id}] {r.summary}\n"

            await message.answer(response)

        finally:
            session.close()
