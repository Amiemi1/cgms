import asyncio
from datetime import datetime

from sqlmodel import select

from app.core.logger import logger
from app.db.session import SessionLocal
from app.db.models.memory import Memory


async def run_reminder_scheduler(bot):
    while True:
        session = SessionLocal()

        try:
            now = datetime.now()

            memories = session.exec(
                select(Memory).where(
                    Memory.reminder_time <= now,
                    Memory.reminder_sent == False
                )
            ).all()

            if memories:
                for m in memories:
                    try:
                        await bot.send_message(
                            m.chat_id,
                            f"⏰ Reminder:\n{m.summary}"
                        )
                        m.reminder_sent = True
                        session.add(m)

                    except Exception:
                        logger.error("REMINDER SEND ERROR", exc_info=True)

                session.commit()

            else:
                logger.info("No due reminders")

        except Exception:
            logger.error("REMINDER SCHEDULER ERROR", exc_info=True)

        finally:
            session.close()

        await asyncio.sleep(10)