from aiogram import F
from aiogram.types import Message

from app.db.session import SessionLocal
from app.services.context.context_service import (
    set_context,
    get_context,
    clear_context
)


def register_context_handlers(dp):

    # ------------------------------------------------
    # SET CONTEXT
    # ------------------------------------------------
    @dp.message(F.text.startswith("/context "))
    async def set_context_handler(message: Message):

        session = SessionLocal()

        try:

            context = message.text.split(" ", 1)[1]

            set_context(
                session,
                message.chat.id,
                context
            )

            await message.answer(
                f"Context set:\n\n{context}"
            )

        finally:
            session.close()


    # ------------------------------------------------
    # VIEW CONTEXT
    # ------------------------------------------------
    @dp.message(F.text == "/context")
    async def view_context_handler(message: Message):

        session = SessionLocal()

        try:

            context = get_context(session, message.chat.id)

            if context:
                await message.answer(
                    f"Current context:\n\n{context}"
                )
            else:
                await message.answer(
                    "No active context."
                )

        finally:
            session.close()


    # ------------------------------------------------
    # CLEAR CONTEXT
    # ------------------------------------------------
    @dp.message(F.text == "/context_clear")
    async def clear_context_handler(message: Message):

        session = SessionLocal()

        try:

            clear_context(
                session,
                message.chat.id
            )

            await message.answer("Context cleared.")

        finally:
            session.close()