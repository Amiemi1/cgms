import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery

from sqlmodel import select

from app.core.config import settings
from app.core.logger import logger

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.candidate_memory import CandidateMemory

from app.services.detection.orchestrator import detect
from app.services.retrieval.query_engine import run_query
from app.services.retrieval.daily_briefing import generate_executive_briefing
from app.services.retrieval.embedding_service import generate_embedding

from app.services.product.product_commands import (
    generate_summary,
    generate_list,
    generate_search
)

from app.services.learning.learning_engine import record_action
from app.services.time_parser.parser import extract_time_safe

from app.bot.keyboards.candidate_actions import candidate_keyboard

from app.services.scheduler.reminder_scheduler import run_reminder_scheduler
from app.services.scheduler.daily_briefing_scheduler import run_daily_briefing_scheduler


bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# =========================
# START
# =========================
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("🤖 CGMS Bot is running.")
    logger.info("Bot started")


# =========================
# ASK (LLM)
# =========================
@dp.message(F.text.startswith("/ask"))
async def ask_handler(message: Message):
    session = SessionLocal()
    try:
        query = message.text.replace("/ask", "").strip()

        if not query:
            await message.answer("Please provide a query.")
            return

        response = run_query(session, message.chat.id, query)
        await message.answer(response)

    except Exception:
        logger.error("ASK ERROR", exc_info=True)
        await message.answer("Error processing query.")

    finally:
        session.close()


# =========================
# BRIEF
# =========================
@dp.message(F.text == "/brief")
async def brief_handler(message: Message):
    session = SessionLocal()
    try:
        memories = session.exec(
            select(Memory).where(Memory.chat_id == message.chat.id)
        ).all()

        result = generate_executive_briefing(memories)
        await message.answer(result)

    except Exception:
        logger.error("BRIEF ERROR", exc_info=True)
        await message.answer("Error generating briefing.")

    finally:
        session.close()


# =========================
# SUMMARY
# =========================
@dp.message(F.text == "/summary")
async def summary_handler(message: Message):
    session = SessionLocal()
    try:
        result = generate_summary(session, message.chat.id)
        await message.answer(result)

    except Exception:
        logger.error("SUMMARY ERROR", exc_info=True)
        await message.answer("Error generating summary.")

    finally:
        session.close()


# =========================
# LIST
# =========================
@dp.message(F.text == "/list")
async def list_handler(message: Message):
    session = SessionLocal()
    try:
        result = generate_list(session, message.chat.id)
        await message.answer(result)

    except Exception:
        logger.error("LIST ERROR", exc_info=True)
        await message.answer("Error generating list.")

    finally:
        session.close()


# =========================
# SEARCH
# =========================
@dp.message(F.text.startswith("/search"))
async def search_handler(message: Message):
    session = SessionLocal()
    try:
        query = message.text.replace("/search", "").strip()

        if not query:
            await message.answer("Please provide a search query.")
            return

        result = generate_search(session, message.chat.id, query)
        await message.answer(result)

    except Exception:
        logger.error("SEARCH ERROR", exc_info=True)
        await message.answer("Error performing search.")

    finally:
        session.close()


# =========================
# DETECTION (IMPORTANT FIX)
# =========================
@dp.message(~F.text.startswith("/"))   # 🔥 DO NOT TOUCH
async def message_handler(message: Message):
    session = SessionLocal()
    try:
        result = detect(message.text)

        if not result:
            return

        candidate = CandidateMemory(
            chat_id=message.chat.id,
            message_id=message.message_id,
            summary=result["summary"],
            memory_type=result["type"],
            original_text=message.text,
            status="pending"
        )

        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        await message.answer(
            f"Save this?\n\n{candidate.summary}",
            reply_markup=candidate_keyboard(candidate.id)
        )

    except Exception:
        logger.error("DETECTION ERROR", exc_info=True)

    finally:
        session.close()


# =========================
# BUTTON HANDLER
# =========================
@dp.callback_query()
async def handle_buttons(callback: CallbackQuery):
    session = SessionLocal()
    try:
        data = callback.data
        action, target_id = data.split(":")
        target_id = int(target_id)

        if action == "save":
            candidate = session.get(CandidateMemory, target_id)

            if not candidate:
                await callback.message.answer("Candidate not found.")
                return

            existing = session.exec(
                select(Memory).where(
                    Memory.chat_id == candidate.chat_id,
                    Memory.summary == candidate.summary
                )
            ).first()

            if existing:
                await callback.message.answer("⚠️ Already exists")
                return

            parsed_time = extract_time_safe(candidate.summary)
            embedding = generate_embedding(candidate.summary)

            memory = Memory(
                chat_id=candidate.chat_id,
                source_message_id=candidate.message_id,
                summary=candidate.summary,
                memory_type=candidate.memory_type,
                reminder_time=parsed_time,
                priority=50,
                embedding=embedding
            )

            session.add(memory)
            session.commit()

            await callback.message.answer(f"✅ Memory saved:\n\n{memory.summary}")

        elif action == "ignore":
            await callback.message.answer("Ignored")

        elif action == "done_memory":
            record_action(session, callback.message.chat.id, target_id, "completed")
            await callback.message.answer("✅ Marked as completed")

        elif action == "delay_memory":
            record_action(session, callback.message.chat.id, target_id, "delayed")
            await callback.message.answer("⏳ Marked as delayed")

    except Exception:
        logger.error("BUTTON ERROR", exc_info=True)
        await callback.answer("Error occurred")

    finally:
        session.close()


# =========================
# MAIN
# =========================
async def main():
    logger.info("🤖 Bot + Scheduler + Daily Briefing running...")

    asyncio.create_task(run_reminder_scheduler(bot))
    asyncio.create_task(run_daily_briefing_scheduler(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())