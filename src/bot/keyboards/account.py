from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def account_kb(user_tg_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="🔄 Обновить", callback_data=f"menu_ua_btn:{user_tg_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад", callback_data=f"menu_back_btn:{user_tg_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
