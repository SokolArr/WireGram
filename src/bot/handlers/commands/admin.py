from aiogram.types import Message

from ...keyboards.admin import admin_menu_kb
from modules.db import DbManager

dbm = DbManager()


async def admin_cmd(message: Message) -> None:
    user = await dbm.get_user(message.from_user.id)
    if user:
        if user.admin_flg:
            await message.answer(
                "Админ-меню для тебя, мой друг",
                reply_markup=admin_menu_kb(user.user_tg_id),
            )
        else:
            await message.answer("УхОди отсюдОва...")
