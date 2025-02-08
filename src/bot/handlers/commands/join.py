from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import html, Bot
from datetime import datetime

from ...keyboards.admin import access_request_kb
from modules.db import DbManager, ReturnCode
from modules.db.models import UserAccCode
from settings import settings

dbm = DbManager()
bot = Bot(
    settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


async def join_cmd(message: Message) -> None:
    user = await dbm.get_user(message.from_user.id)

    admins_id = list(set([settings.TG_ADMIN_ID] + (await dbm.get_admins())))
    if user:
        user_access = await dbm.get_access(
            user.user_tg_id, UserAccCode.BOT.value
        )
        if user_access:
            user_access_valid_to_str = user_access.valid_to_dttm.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if datetime.now() > user_access.valid_to_dttm:
                acc_req_resp = await dbm.add_access_request(
                    user.user_tg_id, UserAccCode.BOT.value
                )
                if acc_req_resp == ReturnCode.SUCCESS:
                    for admin_id in admins_id:
                        await bot.send_message(
                            admin_id,
                            html.bold(
                                "🚨 ВНИМАНИЕ!\nСООБЩЕНИЕ АДМИНИСТРАТОРУ\n"
                            )
                            + f"Поступил запрос на продление доступа (от "
                            f"{user_access_valid_to_str}) "
                            f"к боту для пользователя @{user.user_tag} ("
                            f"{user.user_tg_id})",
                            reply_markup=access_request_kb(user.user_tg_id),
                        )
                    await message.answer(
                        f"⚠️ У тебя закончился доступ к боту "
                        f"{html.bold(user_access_valid_to_str)}, "
                        "и я направил новый запрос на доступ ⏳"
                    )
                elif acc_req_resp == ReturnCode.UNIQUE_VIOLATION:
                    await message.answer(
                        "🕒 Ты уже запрашивал доступ. Дождись его одобрения!"
                    )
            else:
                await message.answer(
                    f"✅ Твой доступ действует до "
                    f"{html.bold(user_access_valid_to_str)}"
                )
        else:
            acc_req_resp = await dbm.add_access_request(
                user.user_tg_id, UserAccCode.BOT.value
            )
            if acc_req_resp == ReturnCode.SUCCESS:
                for admin_id in admins_id:
                    await bot.send_message(
                        admin_id,
                        html.bold("🚨 ВНИМАНИЕ! СООБЩЕНИЕ АДМИНИСТРАТОРУ\n")
                        + f"Поступил запрос на получение доступа к боту от "
                        f"нового пользователя "
                        f"@{user.user_tag} ({user.user_tg_id})",
                        reply_markup=access_request_kb(user.user_tg_id),
                    )
                await message.answer(
                    "📨 Направил запрос на доступ к боту. Ожидай одобрения! ⏳"
                )
            elif acc_req_resp == ReturnCode.UNIQUE_VIOLATION:
                await message.answer(
                    "🕒 Ты уже запрашивал доступ. Дождись его одобрения!"
                )
    else:
        await message.answer(
            "🤔 Я тебя не знаю, жми /start и будем знакомы! 👋"
        )
