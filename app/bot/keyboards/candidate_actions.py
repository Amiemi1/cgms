from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def candidate_keyboard(cid: int):
    """
    Keyboard for memory candidate actions.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Save",
                    callback_data=f"save:{cid}"
                ),
                InlineKeyboardButton(
                    text="❌ Ignore",
                    callback_data=f"ignore:{cid}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✔️ Done",
                    callback_data=f"done_memory:{cid}"
                ),
                InlineKeyboardButton(
                    text="⏳ Delay",
                    callback_data=f"delay_memory:{cid}"
                ),
            ],
        ]
    )