from aiogram.types import Message
from datetime import datetime

from modules.db import DbManager
from ...keyboards.menu import menu_kb

dbm = DbManager()

async def menu_cmd(message: Message) -> None:
    user = await dbm.get_user(message.from_user.id)
    if user:
        user_access = await dbm.get_access(user.user_tg_id, 'BOT')
        if user_access:
            if (user_access.valid_from_dttm < datetime.now()) and (datetime.now() < user_access.valid_to_dttm):
                await message.answer('Вот, что я могу для тебя сделать', reply_markup=menu_kb(user.user_tg_id))
            else:
                await message.answer('У тебя закончился доступ к боту. Нажми /join, чтобы его получить')
        else:
            await message.answer('У тебя нет доступа к боту. Нажми /join, чтобы его получить')
    else:
        await message.answer('Я тебя не знаю, жми /start и будем знакомы!')