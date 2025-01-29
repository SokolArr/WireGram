import logging
import uuid
from datetime import datetime, timedelta
from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import html, Bot

from ...keyboards.menu import menu_kb
from ...keyboards.service import (
    actions_conf_kb, service_back_btn, service_del_view,
    new_order_view, new_conf_view, services_kb
)
from ...keyboards.admin import conf_pay_request_kb
from modules.xui import VlessClientApi, VlessInboundApi
from modules.db import DbManager, ReturnCode
from settings import settings

dbm = DbManager()
bot = Bot(settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
logger = logging.getLogger(__name__)


async def update_user_config_cached_data(user_tg_id, config_name):
    """
    Update cached data for a user's configuration.

    Args:
        user_tg_id (int): The user's Telegram ID.
        config_name (str): The name of the configuration.
    """
    config_path = await VlessClientApi().get_vless_client_link_by_email(config_name)
    conf_expired_dttm = await VlessClientApi().get_client_expired_datetime_by_email(config_name)
    if config_path and conf_expired_dttm:
        cached_data = {
            'config_path': config_path,
            'config_path_add_dttm': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'conf_expired_dttm': conf_expired_dttm.strftime("%Y-%m-%d %H:%M:%S")
        }
        await dbm.update_service_config(user_tg_id, config_name, cached_data=cached_data)


async def serv_cb_cmd(call: CallbackQuery):
    """
    Handle callback queries related to service actions.

    Args:
        call (CallbackQuery): The callback query from the user.
    """
    try:
        call_tag = call.data.split(':')[0]
        user_tg_id = int(call.data.split(':')[1])
        config_name = call.data.split(':')[2]  # TODO: Add proper parsing

        print(call_tag, user_tg_id, config_name)
        match call_tag:
            case 'serv_chosse_btn':
                user_new_order = await dbm.get_order(user_tg_id, config_name, 'NEW')
                user_payed_order = await dbm.get_order(user_tg_id, config_name, 'PAYED')
                if user_new_order:
                    await call.message.edit_text(
                        f'Нашел новый заказ на оплату конфига {config_name} от '
                        f'{user_new_order.sys_inserted_dttm.strftime("%Y-%m-%d %H:%M:%S")}, оплати его',
                        reply_markup=actions_conf_kb(user_tg_id, config_name, is_pay_req=True)
                    )
                elif user_payed_order:
                    await call.message.edit_text(
                        f'Нашел оплаченный заказ по конфигу {config_name} от '
                        f'{user_payed_order.sys_updated_dttm.strftime("%Y-%m-%d %H:%M:%S")}, '
                        'дождись его подтверждения',
                        reply_markup=actions_conf_kb(user_tg_id, config_name)
                    )
                else:
                    await call.message.edit_text(
                        f'Вот что можно сделать с конфигом {config_name}',
                        reply_markup=actions_conf_kb(user_tg_id, config_name, is_renew_req=True)
                    )

            case 'serv_renew_btn':
                resp = await dbm.add_order(user_tg_id, config_name)
                if resp == ReturnCode.SUCCESS:
                    await call.message.edit_text(
                        'Сформировал новый заказ на оплату',
                        reply_markup=new_order_view(user_tg_id, config_name)
                    )
                elif resp == ReturnCode.UNIQUE_VIOLATION:
                    await call.message.edit_text(
                        'Заказ по конфигу уже был сформирован',
                        reply_markup=service_back_btn(user_tg_id, config_name)
                    )
                else:
                    await call.message.edit_text(
                        'Ошибка формирования заказа',
                        reply_markup=service_back_btn(user_tg_id, config_name)
                    )

            case 'serv_payed_btn':
                resp = await dbm.update_order_status(user_tg_id, config_name, 'NEW', 'PAYED')
                if resp == ReturnCode.SUCCESS:
                    await call.message.edit_text(
                        'Обновил статус заказа, дождись, пожалуйста, подтверждения оплаты',
                        reply_markup=service_back_btn(user_tg_id, config_name)
                    )
                    admins_id = list(set([settings.TG_ADMIN_ID] + (await dbm.get_admins())))
                    for admin_id in admins_id:
                        await bot.send_message(
                            admin_id,
                            html.bold("ВНИМАНИЕ!\nСООБЩЕНИЕ АДМИНИСТРАТОРУ\n") +
                            f'Пользователь {user_tg_id} совершил оплату по конфигу {config_name}',
                            reply_markup=conf_pay_request_kb(user_tg_id, config_name)
                        )
                else:
                    await call.message.edit_text(
                        'Ошибка обновления статуса заказа',
                        reply_markup=service_back_btn(user_tg_id, config_name)
                    )

            case 'serv_get_new_btn':
                user_service_configs = await dbm.get_service_configs(user_tg_id)
                conf_tag = 'VLESS'
                expired_delta_days = 14
                max_config_n = 0
                for config in user_service_configs:
                    n = int(config.config_name.split(f'{user_tg_id}_')[1])
                    if n > max_config_n:
                        max_config_n = n
                config_name = f'{conf_tag}_{user_tg_id}_{max_config_n + 1}'
                await call.message.edit_text('Создаю...')
                try:
                    inbound_id = await VlessInboundApi().make_vless_inbound(
                        settings.XUI_VLESS_REMARK, settings.XUI_VLESS_PORT
                    )
                    client_email = await VlessClientApi().make_vless_client(inbound_id, config_name)
                    if client_email:
                        user_service_id = await VlessClientApi().get_client_uuid_by_email(config_name)
                        upd_resp = await VlessClientApi().update_client_expired_time(
                            config_name, datetime.now() + timedelta(expired_delta_days)
                        )
                        if upd_resp:
                            resp = await dbm.add_service_config(
                                user_tg_id, user_service_id, config_name, expired_delta_days=expired_delta_days
                            )
                            if resp == ReturnCode.SUCCESS:
                                await update_user_config_cached_data(user_tg_id, config_name)
                                await call.message.edit_text(
                                    f'Сформировал для тебя конфиг {config_name} и предоставил 14 тестовых дней',
                                    reply_markup=new_conf_view(user_tg_id, config_name)
                                )
                            else:
                                await call.message.edit_text(
                                    f'Ошибка добавления конфига {config_name}',
                                    reply_markup=services_kb(user_tg_id, user_service_configs)
                                )
                except Exception as e:
                    await call.message.edit_text(
                        f'Ошибка добавления конфига {config_name}',
                        reply_markup=menu_kb(user_tg_id)
                    )
                    raise e

            case 'serv_del_conf_btn':
                resp = await dbm.delete_service_config(user_tg_id, config_name)
                if resp == ReturnCode.SUCCESS:
                    await VlessClientApi().delete_client(config_name)
                    await call.message.edit_text(
                        f'Удалил твой конфиг {config_name}',
                        reply_markup=service_del_view(user_tg_id)
                    )
                else:
                    await call.message.edit_text(
                        f'Не смог удалить твой конфиг {config_name}',
                        reply_markup=service_back_btn(user_tg_id, config_name)
                    )

            case 'serv_get_path_btn':
                config_path = ''
                user_service_config = await dbm.get_service_config(user_tg_id, config_name)
                if user_service_config:
                    cached_config_path = user_service_config.cached_data.get('config_path')
                    cached_config_path_add_dttm = user_service_config.cached_data.get('config_path_add_dttm')

                    if cached_config_path_add_dttm:
                        cached_config_path_add_dttm = datetime.strptime(
                            cached_config_path_add_dttm, "%Y-%m-%d %H:%M:%S"
                        )
                        if cached_config_path_add_dttm + timedelta(3) > datetime.now():
                            if cached_config_path:
                                config_path = cached_config_path
                            else:
                                config_path = await VlessClientApi().get_vless_client_link_by_email(config_name)
                                await update_user_config_cached_data(user_tg_id, config_name)
                        else:
                            config_path = await VlessClientApi().get_vless_client_link_by_email(config_name)
                            await update_user_config_cached_data(user_tg_id, config_name)
                    else:
                        config_path = await VlessClientApi().get_vless_client_link_by_email(config_name)
                        await update_user_config_cached_data(user_tg_id, config_name)
                    await call.message.edit_text(
                        f'Вот ссылка для тебя. Вставь ее в приложении\n\n{html.code(config_path)}',
                        reply_markup=service_back_btn(user_tg_id, config_name)
                    )

    except Exception as e:
        logger.error(f'{e}')
    finally:
        await call.answer()