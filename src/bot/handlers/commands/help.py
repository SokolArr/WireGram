from aiogram.types import Message

from modules.db import DbManager

dbm = DbManager()

async def help_cmd(message: Message) -> None:
    resp = await dbm.get_user(message.from_user.id)
    if resp:
        mess = (f"✅ Чтобы получить доступ к боту, нажми команду /join.\n\
🔤 Все доступные действия можно найти в меню, используя команду \
/menu.\nℹ️ Если тебе нужна помощь с ботом или возникла ошибка,\
пожалуйста, напиши в группу: https://t.me/c/2218172872.")
        await message.answer(mess)
    else:
        await message.answer('Я тебя не знаю, жми /start и будем знакомы!')