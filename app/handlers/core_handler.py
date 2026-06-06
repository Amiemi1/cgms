from aiogram import F
from aiogram.types import Message
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory

from app.services.agent.agent_orchestrator import run_agent
from app.services.context.context_service import get_context
from app.services.intelligence.memory_intelligence_service import rank_memories


def register_core_handlers(dp):

    @dp.message(F.text == "/start")
    async def start(message: Message):
        await message.answer("🤖 CGMS Bot is running.")


    @dp.message(F.text == "/whoami")
    async def whoami(message: Message):
        await message.answer(str(message.from_user.id))


    @dp.message(F.text.startswith("/ask "))
    async def ask_handler(message: Message):

        session = SessionLocal()

        try:

            chat_id = message.chat.id
            query = message.text.split(" ",1)[1]

            context = get_context(session, chat_id)

            memories = session.exec(
                select(Memory)
                .where(Memory.chat_id == chat_id)
                .limit(50)
            ).all()

            memories = rank_memories(memories, query, context)

            if not memories:
                await message.answer("No memories stored yet.")
                return

            response = "Relevant memories:\n\n"

            for m in memories[:5]:
                response += f"• {m.summary}\n"

            await message.answer(response)

        finally:
            session.close()


    @dp.message(F.text.startswith("/plan"))
    async def plan_handler(message: Message):

        session = SessionLocal()

        try:
            goal = message.text.replace("/plan","").strip()
            response = run_agent(session, message.chat.id, goal)
            await message.answer(response)

        finally:
            session.close()