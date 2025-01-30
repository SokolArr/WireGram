from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def menu_kb(user_tg_id: int):
    kb = [
        [InlineKeyboardButton(text="💼 Личный кабинет", callback_data=f'menu_ua_btn:{user_tg_id}')],
        [InlineKeyboardButton(text="🌎 Доступ к сервису", callback_data=f'menu_service_btn:{user_tg_id}')],
        # [InlineKeyboardButton(text="⚙️ Настройки", callback_data=f'menu_pref_btn:{user_tg_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)