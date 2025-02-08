from aiogram import html
from aiogram.types import Message

from settings import settings

from modules.db import DbManager, ReturnCode
from modules.db.models import UserStruct

dbm = DbManager()


async def start_cmd(message: Message) -> None:
    user_struct = UserStruct(
        user_tg_id=message.from_user.id,
        user_name=message.from_user.full_name,
        user_tag=message.from_user.username,
        admin_flg=(message.from_user.id == settings.TG_ADMIN_ID),
        lang_code=message.from_user.language_code.upper(),
    )

    resp = await dbm.add_user(user_struct)
    if resp == ReturnCode.SUCCESS:
        is_admin_str = (
            "администратор "
            if (message.from_user.id == settings.TG_ADMIN_ID)
            else ""
        )
        await message.answer(
            f"Приятно 🤝 познакомиться, {is_admin_str}"
            + f"{html.bold(message.from_user.full_name)}\n"
            + "✅ Нажми /join чтобы запросить доступ к боту\n"
            + "😑 Нажми /help если тебе непонятно, что делать\n"
            + "🔤 Нажми /menu чтобы открыть меню\n"
        )
    elif resp == ReturnCode.UNIQUE_VIOLATION:
        await message.answer(
            f"И снова 👋 привет, {html.bold(message.from_user.full_name)}\n"
            + "✅ Нажми /join чтобы запросить доступ к боту\n"
            + "😑 Нажми /help если тебе непонятно, что делать\n"
            + "🔤 Нажми /menu чтобы открыть меню\n"
        )
    else:
        raise BaseException(
            f"ERROR ADD NEW USER {message.from_user.id} TO DATABASE"
        )
