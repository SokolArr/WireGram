import logging
from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import html, Bot

from ...keyboards.menu import menu_kb
from ...keyboards.account import account_kb
from ...keyboards.service import new_service_kb, services_kb
from modules.db import DbManager, ReturnCode
from settings import settings

dbm = DbManager()
bot = Bot(settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
logger = logging.getLogger(__name__)

async def menu_cb_cmd(call: CallbackQuery):
    try:
        call_tag = call.data.split(':')[0]
        user_tg_id = int(call.data.split(':')[1])

        match call_tag:
            case 'menu_ua_btn':
                user_configs = await dbm.get_service_configs(user_tg_id)
                conf_mess = ''
                if user_configs:
                    conf_mess += '\n- Конфигурации\n'
                    for idx, conf in enumerate(user_configs):
                        conf_mess += f'  - {idx + 1}. {conf.config_name}\n'
                bot_access = await dbm.get_access(user_tg_id, 'BOT')
                mess = (
                    html.bold('Личный кабинет\n') +
                    f'\n- Доступ к боту дествителен до {bot_access.valid_to_dttm.strftime("%Y-%m-%d %H:%M:%S")}' +
                    f'{conf_mess}'
                )
                try:
                    await call.message.edit_text(mess, reply_markup=account_kb(user_tg_id))
                except Exception as e:
                    logger.debug(f'CANT EDIT MESSAGE BECAUSE: {e}')
            
            case 'menu_service_btn':
                user_configs = await dbm.get_service_configs(user_tg_id)
                if user_configs:
                    conf_mess = '\n'
                    for idx, conf in enumerate(user_configs):
                        conf_mess += f'{idx + 1}. {conf.config_name} (активна до {conf.valid_to_dttm.strftime("%Y-%m-%d %H:%M:%S")})\n'
                    mess = (
                        html.bold(f'Конфигурации ({len(user_configs)}/3)\n') +
                        conf_mess
                    )
                    await call.message.edit_text(mess, reply_markup=services_kb(user_tg_id, user_configs))
                else:
                    await call.message.edit_text(f'Не нашел твоих конфигов', reply_markup=new_service_kb(user_tg_id))
                    logger.debug(f'NO USER {user_tg_id} CONFIGS')
            
            case 'menu_pref_btn':
                pass
            
            case 'menu_back_btn':
                await call.message.edit_text('Вот что я могу для тебя сделать', reply_markup=menu_kb(user_tg_id))
            
    except Exception as e:
           logger.error(f'{e}')
    finally:
        await call.answer()