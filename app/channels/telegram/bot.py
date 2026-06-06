from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

import requests

from app.core.config import settings


bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


API_URL = "http://localhost:8000/ingest/message"


@dp.message()
async def handle_message(message: Message):

    payload = {
        "channel": "telegram",
        "user_id": str(message.chat.id),
        "text": message.text
    }

    response = requests.post(API_URL, json=payload)

    result = response.json()

    if result["result"]["type"] != "none":
        await message.answer(
            f"Memory captured: {result['result']['type']}"
        )