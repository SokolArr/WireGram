from aiogram.types import Message

from modules.db import DbManager

dbm = DbManager()

async def help_cmd(message: Message) -> None:
    resp = await dbm.get_user(message.from_user.id)
    if resp:
        mess = (
            "✅ Чтобы получить доступ к боту, нажми команду /join.\n"
            "📋 Все доступные действия можно найти в меню, используя команду /menu.\n"
            "ℹ️ Если тебе нужна помощь с ботом или возникла ошибка, пожалуйста, напиши в группу: "
            "<a href='https://t.me/+z4RCgyLfgvdkNTli'>👉 Наша группа поддержки</a>"
        )
        await message.answer(mess, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await message.answer('🤔 Я тебя не знаю, жми /start и будем знакомы! 👋')