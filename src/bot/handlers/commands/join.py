from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import html, Bot
from datetime import datetime

from ...keyboards.admin import access_request_kb
from modules.db import DbManager, ReturnCode
from settings import settings

dbm = DbManager()
bot = Bot(settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def join_cmd(message: Message) -> None:
    user = await dbm.get_user(message.from_user.id)
    
    admins_id = list(set([settings.TG_ADMIN_ID] + (await dbm.get_admins())))
    if user:
        user_access = await dbm.get_access(user.user_tg_id, 'BOT')
        if user_access:
            if datetime.now() > user_access.valid_to_dttm:
                acc_req_resp = await dbm.add_access_request(user.user_tg_id, 'BOT')
                if acc_req_resp == ReturnCode.SUCCESS:
                    for admin_id in admins_id:
                        await bot.send_message(admin_id, html.bold("ВНИМАНИЕ!\nСООБЩЕНИЕ АДМИНИСТРАТОРУ") + 
                                               f'\n\nПоступил запрос на продление доступа (от {user_access.valid_to_dttm.strftime("%Y-%m-%d %H:%M:%S")}) к боту для пользователя @{user.user_tag}({user.user_tg_id})', reply_markup=access_request_kb(user.user_tg_id))
                    await message.answer(f'У тебя закончился доступ к боту {html.bold(user_access.valid_to_dttm.strftime("%Y-%m-%d %H:%M:%S"))}, и я направил новый запрос на доступ')
                elif acc_req_resp == ReturnCode.UNIQUE_VIOLATION:
                    await message.answer('Ты уже запрашивал доступ. Дождись его одобрения!')
            else:
                await message.answer(f'Твой доступ действует до {html.bold(user_access.valid_to_dttm.strftime("%Y-%m-%d %H:%M:%S"))}')
        else:
            acc_req_resp = await dbm.add_access_request(user.user_tg_id, 'BOT')
            if acc_req_resp == ReturnCode.SUCCESS:
                for admin_id in admins_id:
                    await bot.send_message(admin_id, html.bold("ВНИМАНИЕ!\nСООБЩЕНИЕ АДМИНИСТРАТОРУ") + 
                                           f'\n\nПоступил запрос на получение доступа к боту от нового пользователя @{user.user_tag}({user.user_tg_id})', reply_markup=access_request_kb(user.user_tg_id))
                await message.answer('Направил запрос на доступ к боту')
            elif acc_req_resp == ReturnCode.UNIQUE_VIOLATION:
                await message.answer('Ты уже запрашивал доступ. Дождись его одобрения!')
    else:
        await message.answer('Я тебя не знаю, жми /start и будем знакомы!')