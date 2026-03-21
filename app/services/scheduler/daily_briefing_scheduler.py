import asyncio
from datetime import datetime

from sqlmodel import select

from app.core.logger import logger
from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.services.retrieval.daily_briefing import generate_executive_briefing


async def run_daily_briefing_scheduler(bot):
    last_run_date = None

    while True:
        session = SessionLocal()

        try:
            now = datetime.now()

            if now.hour == 9 and last_run_date != now.date():
                logger.info("Running daily briefing...")

                memories = session.exec(select(Memory)).all()

                if memories:
                    briefing = generate_executive_briefing(memories)
                    chat_ids = list(set([m.chat_id for m in memories]))

                    for chat_id in chat_ids:
                        try:
                            await bot.send_message(chat_id, briefing)
                        except Exception:
                            logger.error("BRIEF SEND ERROR", exc_info=True)

                last_run_date = now.date()

        except Exception:
            logger.error("DAILY BRIEFING ERROR", exc_info=True)

        finally:
            session.close()

        await asyncio.sleep(60)