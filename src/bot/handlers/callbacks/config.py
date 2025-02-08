from datetime import datetime, timedelta
from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import html, Bot

from ...keyboards.menu import menu_kb
from ...keyboards.service import (
    actions_conf_kb,
    service_back_btn,
    service_del_view,
    new_order_view,
    new_conf_view,
)
from ...keyboards.admin import conf_pay_request_kb
from modules.xui import VlessClientApi, VlessInboundApi
from modules.db import DbManager, ReturnCode
from modules.db.models import OrderStatus, get_order_nm_str
from settings import settings
from logger import MainLogger, get_error_timestamp

dbm = DbManager()
bot = Bot(
    settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
logger = MainLogger(__name__).get()


async def choose_conf(call: CallbackQuery, user_tg_id: int, config_name: str):
    try:
        user_new_order = await dbm.get_order(
            user_tg_id, config_name, OrderStatus.NEW.value
        )
        user_payed_order = await dbm.get_order(
            user_tg_id, config_name, OrderStatus.PAYED.value
        )
        if user_new_order:
            order_short_nm = html.code(get_order_nm_str(user_new_order))
            order_cost = user_new_order.order_data.get("config_price")
            sys_inserted_dttm = user_new_order.sys_inserted_dttm
            await call.message.edit_text(
                f"🔍 Нашел 🆕 новый заказ ({order_short_nm}) "
                f"на оплату конфига {config_name} от "
                f"{sys_inserted_dttm.strftime("%Y-%m-%d %H:%M:%S")}"
                f", оплати 💳 {order_cost}₽ ",
                reply_markup=actions_conf_kb(
                    user_tg_id, config_name, is_pay_req=True
                ),
            )
        elif user_payed_order:
            order_short_nm = html.code(get_order_nm_str(user_payed_order))
            sys_updated_dttm = user_payed_order.sys_updated_dttm
            await call.message.edit_text(
                f"🔍 Нашел 💵 оплаченный заказ ({order_short_nm}) "
                f"по конфигу {config_name} от "
                f"{sys_updated_dttm.strftime("%Y-%m-%d %H:%M:%S")}, "
                "пожалуйста, дождись его подтверждения ⏳",
                reply_markup=actions_conf_kb(user_tg_id, config_name),
            )
        else:
            await call.message.edit_text(
                f"✨ Вот что можно сделать с конфигом {config_name}",
                reply_markup=actions_conf_kb(
                    user_tg_id, config_name, is_renew_req=True
                ),
            )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Не смог выбрать твой конфиг {config_name}"
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=menu_kb(user_tg_id),
        )


async def renew_conf(call: CallbackQuery, user_tg_id: int, config_name: str):
    try:
        resp = await dbm.add_order(user_tg_id, config_name)
        if resp == ReturnCode.SUCCESS:
            user_new_order = await dbm.get_order(
                user_tg_id, config_name, OrderStatus.NEW.value
            )
            order_cost = user_new_order.order_data.get("config_price")
            order_short_nm = html.code(get_order_nm_str(user_new_order))
            await call.message.edit_text(
                f"🛒 Сформировал новый заказ ({order_short_nm})"
                f", оплати 💳 {order_cost}₽",
                reply_markup=new_order_view(user_tg_id, config_name),
            )
        elif resp == ReturnCode.UNIQUE_VIOLATION:
            await call.message.edit_text(
                "⚠️ Заказ по конфигу уже был сформирован",
                reply_markup=service_back_btn(user_tg_id, config_name),
            )
        else:
            raise BaseException(
                f"BAD TRY TO RENEW CONF {config_name} FOR USER {user_tg_id}"
            )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Ошибка формирования заказа " f"{user_tg_id} {config_name}"
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=service_back_btn(user_tg_id, config_name),
        )


async def pay_conf(call: CallbackQuery, user_tg_id: int, config_name: str):
    try:
        db_user = await dbm.get_user(user_tg_id)
        resp = await dbm.update_order_status(
            user_tg_id,
            config_name,
            OrderStatus.NEW.value,
            OrderStatus.PAYED.value,
        )
        if resp == ReturnCode.SUCCESS:
            await call.message.edit_text(
                "✅ Обновил статус заказа, дождись, пожалуйста, "
                "подтверждения оплаты ⏳",
                reply_markup=service_back_btn(user_tg_id, config_name),
            )
            admins_id = list(
                set([settings.TG_ADMIN_ID] + (await dbm.get_admins()))
            )
            for admin_id in admins_id:
                await bot.send_message(
                    admin_id,
                    html.bold("🚨 ВНИМАНИЕ! СООБЩЕНИЕ АДМИНИСТРАТОРУ\n")
                    + f"Пользователь @{db_user.user_tag} ({user_tg_id}) "
                    f"совершил оплату по конфигу {config_name}",
                    reply_markup=conf_pay_request_kb(user_tg_id, config_name),
                )
        else:
            raise BaseException(
                f"BAD TRY TO PAY CONF {config_name} FOR USER {user_tg_id}"
            )
    except Exception as e:
        logger.error(e)
        mess = (
            f"❌ Ошибка обновления статуса заказа "
            f"{user_tg_id} {config_name}"
        )
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=service_back_btn(user_tg_id, config_name),
        )


async def new_conf(call: CallbackQuery, user_tg_id: int):
    user_service_configs = await dbm.get_service_configs(user_tg_id)
    conf_tag = "vless"
    expired_delta_days = settings.FREE_CONF_PERIOD_DAYS
    max_config_n = 0
    for config in user_service_configs:
        n = int(config.config_name.split(f"{user_tg_id}_")[1])
        if n > max_config_n:
            max_config_n = n
    config_name = f"{conf_tag}_{user_tg_id}_{max_config_n + 1}"
    await call.message.edit_text("🛠️ Создаю...")
    try:
        free_inbound_port = await VlessInboundApi().get_inbounds_free_port()
        inbound_id = await VlessInboundApi().make_vless_inbound(
            str(user_tg_id), free_inbound_port
        )
        client_email = await VlessClientApi().make_vless_client(
            inbound_id, config_name
        )
        if client_email:
            user_service_id = await VlessClientApi().get_client_uuid_by_email(
                config_name
            )
            upd_resp = await VlessClientApi().update_client_expired_time(
                config_name,
                datetime.now() + timedelta(expired_delta_days),
            )
            if upd_resp:
                resp = await dbm.add_service_config(
                    user_tg_id,
                    user_service_id,
                    config_name,
                    expired_delta_days=expired_delta_days,
                )
                if resp == ReturnCode.SUCCESS:
                    await update_user_config_cached_data(
                        user_tg_id, config_name
                    )
                    await call.message.edit_text(
                        f"🎉 Сформировал для тебя конфиг {config_name} "
                        f"и предоставил {expired_delta_days} 🆓 тестовых дней",
                        reply_markup=new_conf_view(user_tg_id, config_name),
                    )
                else:
                    raise BaseException(
                        f"BAD TRY TO MAKE NEW CONF {config_name} "
                        f"FOR USER {user_tg_id}"
                    )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Ошибка добавления конфига {config_name} для {user_tg_id}"
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=menu_kb(user_tg_id),
        )


async def delete_conf(call: CallbackQuery, user_tg_id: int, config_name: str):
    try:
        resp = await dbm.delete_service_config(user_tg_id, config_name)
        if resp == ReturnCode.SUCCESS:
            await VlessClientApi().delete_client(config_name)
            await call.message.edit_text(
                f"🗑️ Удалил твой конфиг {config_name}",
                reply_markup=service_del_view(user_tg_id),
            )
        else:
            raise BaseException(
                f"BAD TRY TO DELETE CONFIG {config_name} "
                f"FOR USER {user_tg_id}"
            )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Не смог удалить твой конфиг {config_name} "
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=service_back_btn(user_tg_id, config_name),
        )


async def update_user_config_cached_data(user_tg_id: int, config_name: str):
    config_path = await VlessClientApi().get_vless_client_link_by_email(
        config_name
    )
    conf_expired_dttm = (
        await VlessClientApi().get_client_expired_datetime_by_email(
            config_name
        )
    )
    if config_path and conf_expired_dttm:
        cached_data = {
            "config_path": config_path,
            "config_path_add_dttm": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "conf_expired_dttm": conf_expired_dttm.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        await dbm.update_service_config(
            user_tg_id, config_name, cached_data=cached_data
        )


async def get_vless_conf_path(user_tg_id: int, config_name: str):
    config_path = await VlessClientApi().get_vless_client_link_by_email(
        config_name
    )
    await update_user_config_cached_data(user_tg_id, config_name)
    return config_path


async def path_conf(call: CallbackQuery, user_tg_id: int, config_name: str):
    try:
        config_path = ""
        user_service_config = await dbm.get_service_config(
            user_tg_id, config_name
        )
        if user_service_config:
            cached_config_path = user_service_config.cached_data.get(
                "config_path", ""
            )
            cached_config_path_add_dttm = user_service_config.cached_data.get(
                "config_path_add_dttm", ""
            )

            if cached_config_path_add_dttm:
                cached_config_path_add_dttm = datetime.strptime(
                    cached_config_path_add_dttm, "%Y-%m-%d %H:%M:%S"
                )
                if cached_config_path_add_dttm + timedelta(3) > datetime.now():
                    if cached_config_path:
                        config_path = cached_config_path
                    else:
                        config_path = await get_vless_conf_path(
                            user_tg_id, config_name
                        )
                else:
                    config_path = await get_vless_conf_path(
                        user_tg_id, config_name
                    )
            else:
                config_path = await get_vless_conf_path(
                    user_tg_id, config_name
                )
            android_link = settings.VLESS_APP_ANDROID_LINK
            apple_link = settings.VLESS_APP_APPLE_LINK
            pc_link = settings.VLESS_APP_PC_LINK
            all_link = settings.VLESS_APP_ALL_LINK
            mess = (
                "Для того, чтобы воспользоваться ссылкой, "
                "ее необходимо вставить в приложении:\n"
                f"🤖 - для Android: <a href='{android_link}'>ссылка</a>\n"
                f"🍏 - для Apple (iOS): <a href='{apple_link}'>ссылка</a>\n"
                f"💻 - для PC: <a href='{pc_link}'>ссылка</a>\n"
                f"🔗 - все варианты: <a href='{all_link}'>ссылка</a>"
            )
            await call.message.edit_text(
                mess + f"\n\n{html.pre(config_path)}",
                parse_mode="HTML",
                reply_markup=service_back_btn(user_tg_id, config_name),
                disable_web_page_preview=True,
            )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Не смог выдать тебе ссылку {user_tg_id} на {config_name}"
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=service_back_btn(user_tg_id, config_name),
        )


async def serv_cb_cmd(call: CallbackQuery):
    try:
        call_tag = call.data.split(":")[0]
        user_tg_id = int(call.data.split(":")[1])
        config_name = call.data.split(":")[2]

        match call_tag:
            case "serv_chosse_btn":
                await choose_conf(call, user_tg_id, config_name)

            case "serv_renew_btn":
                await renew_conf(call, user_tg_id, config_name)

            case "serv_payed_btn":
                await pay_conf(call, user_tg_id, config_name)

            case "serv_get_new_btn":
                await new_conf(call, user_tg_id)

            case "serv_del_conf_btn":
                await delete_conf(call, user_tg_id, config_name)

            case "serv_get_path_btn":
                await path_conf(call, user_tg_id, config_name)

    except Exception as e:
        logger.error(f"{e}")
    finally:
        await call.answer()
