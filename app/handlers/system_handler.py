from aiogram import F
from aiogram.types import Message

from app.db.session import SessionLocal

from app.services.control.cognitive_control import evaluate_system_state
from app.services.control.brain_engine import get_brain_status
from app.services.intelligence.intelligence_engine import generate_intelligence_report


def register_system_handlers(dp):

    # ------------------------------------------------
    # SYSTEM STATE
    # ------------------------------------------------
    @dp.message(F.text == "/system")
    async def system_handler(message: Message):

        session = SessionLocal()

        try:

            state = evaluate_system_state(
                session=session,
                chat_id=message.chat.id
            )

            response = "⚙ System State\n\n"

            if isinstance(state, dict):

                focus = state.get("focus_topic", "None")
                blocked = state.get("blocked_tasks", [])

                response += f"Focus topic: {focus}\n\n"

                if blocked:

                    response += "Blocked tasks:\n"

                    for t in blocked:
                        response += f"• {t}\n"

                else:

                    response += "No blocked tasks detected."

            else:

                response += str(state)

            await message.answer(response)

        finally:
            session.close()


    # ------------------------------------------------
    # BRAIN STATUS
    # ------------------------------------------------
    @dp.message(F.text == "/brain")
    async def brain_handler(message: Message):

        session = SessionLocal()

        try:

            response = get_brain_status(
                session=session,
                chat_id=message.chat.id
            )

            await message.answer(response)

        finally:
            session.close()


    # ------------------------------------------------
    # DAILY BRIEFING
    # ------------------------------------------------
    @dp.message(F.text == "/briefing")
    async def briefing_handler(message: Message):

        session = SessionLocal()

        try:

            report = generate_intelligence_report(
                session,
                message.chat.id
            )

            await message.answer(report)

        finally:
            session.close()