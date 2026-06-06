from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.db.session import SessionLocal
from app.db.models.candidate_memory import CandidateMemory
from app.db.models.memory import Memory

from app.services.ingestion.message_ingestor import ingest_message
from app.services.security.security_guard import enforce_memory_creation_security
from app.services.retrieval.embedding_service import generate_embedding
from app.services.memory.memory_graph import link_memories
from app.services.reasoning.decision_lineage_service import record_decision_lineage
from app.services.time_parser.parser import extract_time_safe


def register_ingestion_handlers(dp):

    # ------------------------------------------------
    # MESSAGE INGESTION (NON-COMMAND MESSAGES)
    # ------------------------------------------------
    @dp.message(~F.text.startswith("/"))
    async def fallback_handler(message: Message):

        session = SessionLocal()

        try:

            # --------------------------------
            # INGEST MESSAGE
            # --------------------------------

            candidate = ingest_message(
                session=session,
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=message.text
            )

            if not candidate:
                return

            # --------------------------------
            # MEMORY ACTION KEYBOARD
            # --------------------------------

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Save",
                            callback_data=f"save:{candidate.id}"
                        ),
                        InlineKeyboardButton(
                            text="Ignore",
                            callback_data=f"ignore:{candidate.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Delay",
                            callback_data=f"delay:{candidate.id}"
                        ),
                        InlineKeyboardButton(
                            text="Done",
                            callback_data=f"done:{candidate.id}"
                        )
                    ]
                ]
            )

            await message.answer(
                "Save memory?",
                reply_markup=keyboard
            )

        finally:
            session.close()

    # ------------------------------------------------
    # BUTTON HANDLER
    # ------------------------------------------------
    @dp.callback_query()
    async def handle_buttons(callback: CallbackQuery):

        session = SessionLocal()

        try:

            action, candidate_id = callback.data.split(":")
            candidate = session.get(CandidateMemory, int(candidate_id))

            if not candidate:
                await callback.message.answer("Candidate not found.")
                return

            # --------------------------------
            # SECURITY CHECK
            # --------------------------------

            allowed = enforce_memory_creation_security(
                session,
                callback.from_user.id
            )

            if not allowed:
                await callback.message.answer(
                    "You are not authorized to create memory."
                )
                return

            # --------------------------------
            # SAVE MEMORY
            # --------------------------------

            if action == "save":

                parsed_time = extract_time_safe(candidate.summary)

                embedding = generate_embedding(candidate.summary)

                memory = Memory(
                    chat_id=candidate.chat_id,
                    source_message_id=candidate.message_id,
                    summary=candidate.summary,
                    memory_type=candidate.memory_type,
                    status="active",
                    reminder_time=parsed_time,
                    priority=50,
                    reminder_sent=False,
                    embedding=embedding
                )

                session.add(memory)
                session.commit()
                session.refresh(memory)

                # --------------------------------
                # RECORD DECISION LINEAGE
                # --------------------------------

                if memory.memory_type == "decision":

                    record_decision_lineage(
                        session=session,
                        decision_id=memory.id,
                        source_memory_id=None,
                        reasoning_engine="reasoning_engine",
                        triggered_by_user=callback.from_user.id
                    )

                # --------------------------------
                # LINK MEMORY GRAPH
                # --------------------------------

                link_memories(session, memory)

                await callback.message.answer("Memory saved.")
                await callback.answer()

            # --------------------------------
            # IGNORE MEMORY
            # --------------------------------

            elif action == "ignore":

                await callback.message.answer("Memory ignored.")
                await callback.answer()

            # --------------------------------
            # DELAY MEMORY
            # --------------------------------

            elif action == "delay":

                await callback.message.answer(
                    "Memory delayed. You can review it later."
                )
                await callback.answer()

            # --------------------------------
            # MARK AS DONE
            # --------------------------------

            elif action == "done":

                await callback.message.answer(
                    "Marked as completed."
                )
                await callback.answer()

        except Exception as e:

            print("BUTTON HANDLER ERROR:", e)

        finally:

            session.close()