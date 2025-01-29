from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def pref_kb():
    kb = [
        [InlineKeyboardButton(text="Настройка №1", callback_data=f'pref_1_btn:')],
        [InlineKeyboardButton(text="Настройка №2", callback_data=f'pref_2_btn:')],
        [InlineKeyboardButton(text="Настройка №3", callback_data=f'pref_3_btn:')],
        [InlineKeyboardButton(text="Настройка №4", callback_data=f'pref_4_btn:')],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_back_btn:')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)