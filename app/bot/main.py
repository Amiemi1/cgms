# ==============================================================
# CGMS BOT ENTRY POINT
# ==============================================================

import asyncio

from aiogram import Bot, Dispatcher

from app.core.config import settings
from app.core.logger import logger

from app.bot.router import register_handlers

# scheduler services
from app.services.scheduler.reminder_scheduler import run_reminder_scheduler
from app.services.scheduler.daily_briefing_scheduler import run_daily_briefing_scheduler


# ==============================================================
# BOT INITIALIZATION
# ==============================================================

print("CGMS BOT FILE LOADED")

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# ==============================================================
# REGISTER ALL HANDLERS
# ==============================================================

register_handlers(dp)


# ==============================================================
# SCHEDULERS
# ==============================================================

async def start_schedulers():

    logger.info("Starting schedulers...")

    asyncio.create_task(run_reminder_scheduler(bot))
    asyncio.create_task(run_daily_briefing_scheduler(bot))


# ==============================================================
# APPLICATION START
# ==============================================================

async def main():

    print("Starting CGMS Bot...")

    await start_schedulers()

    logger.info("Starting Telegram polling...")

    await dp.start_polling(bot)


# ==============================================================
# ENTRY POINT
# ==============================================================

if __name__ == "__main__":

    asyncio.run(main())