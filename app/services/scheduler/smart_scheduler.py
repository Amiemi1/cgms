import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models.memory import Memory


HIGH_PRIORITY_THRESHOLD = 80
MEDIUM_PRIORITY_THRESHOLD = 50


def fetch_due_memories(session: Session):
    now = datetime.now()

    return session.query(Memory).filter(
        Memory.reminder_time <= now,
        Memory.reminder_sent == False
    ).all()


def sort_by_priority(memories):
    return sorted(memories, key=lambda m: m.priority or 0, reverse=True)


def categorize(memories):
    high, medium, low = [], [], []

    for m in memories:
        if m.priority >= HIGH_PRIORITY_THRESHOLD:
            high.append(m)
        elif m.priority >= MEDIUM_PRIORITY_THRESHOLD:
            medium.append(m)
        else:
            low.append(m)

    return high, medium, low


async def dispatch(memories, bot):
    for m in memories:
        try:
            await bot.send_message(chat_id=m.chat_id, text=m.summary)
            m.reminder_sent = True
        except Exception as e:
            print(f"Error sending message: {e}")


async def run_scheduler(session_factory, bot, interval=10):
    """
    session_factory: function that returns a DB session
    bot: aiogram Bot instance
    interval: seconds between checks
    """

    print("🚀 Smart Scheduler started...")

    while True:
        session = session_factory()

        try:
            memories = fetch_due_memories(session)

            if memories:
                memories = sort_by_priority(memories)
                high, medium, low = categorize(memories)

                print(f"🔥 High: {len(high)}, ⚡ Medium: {len(medium)}, 💤 Low: {len(low)}")

                await dispatch(high, bot)
                await dispatch(medium, bot)
                await dispatch(low, bot)

                session.commit()
            else:
                print("No due reminders")

        except Exception as e:
            print(f"Scheduler error: {e}")

        finally:
            session.close()

        await asyncio.sleep(interval)