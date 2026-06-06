from aiogram import F
from aiogram.types import Message

from app.db.session import SessionLocal

from app.services.reasoning.trace_service import trace_decision
from app.services.reasoning.decision_explain_service import explain_decision


def register_reasoning_handlers(dp):

    @dp.message(F.text.startswith("/trace "))
    async def trace_handler(message: Message):

        session = SessionLocal()

        try:

            query = message.text.split(" ",1)[1]

            result = trace_decision(session,query)

            await message.answer(result)

        finally:
            session.close()


    @dp.message(F.text.startswith("/explain"))
    async def explain_handler(message: Message):

        session = SessionLocal()

        try:

            query = message.text.split(" ",1)[1]

            result = explain_decision(session,query)

            await message.answer(result)

        finally:
            session.close()