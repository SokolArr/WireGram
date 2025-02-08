from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import Bot
from datetime import datetime, timedelta

from ...keyboards.admin import (
    admin_menu_kb,
    all_access_request_btn,
    access_requests_kb,
    all_conf_pay_requests_btn,
    conf_pay_requests_btn,
)
from modules.db import DbManager, ReturnCode
from modules.xui import VlessClientApi
from modules.db.models import OrderStatus, UserAccCode
from settings import settings
from logger import MainLogger, get_error_timestamp

dbm = DbManager()
bot = Bot(
    settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
logger = MainLogger(__name__).get()


async def send_success_bot_sub_user(user_tg_id: int, expired_delta_days: int):
    await bot.send_message(
        user_tg_id,
        "👋 Привет! Тебе одобрили подписку "
        f"для бота на {expired_delta_days} дней🎉\n"
        "Используй /menu, чтобы узнать что можно сделать",
    )


async def accept_bot_access_request(call: CallbackQuery, user_tg_id: int):
    try:
        expired_delta_days = settings.BOT_ACCESS_EXPIRED_DELTA_DAYS
        resp = await dbm.add_access(
            user_tg_id, UserAccCode.BOT.value, expired_delta_days
        )
        if resp == ReturnCode.SUCCESS:
            await call.message.edit_text(
                f"✅ Добавил доступ для {user_tg_id} "
                f"на {expired_delta_days} дней 📅",
                reply_markup=all_access_request_btn(user_tg_id),
            )
            await send_success_bot_sub_user(user_tg_id, expired_delta_days)

        elif resp == ReturnCode.UNIQUE_VIOLATION:
            resp_2 = await dbm.update_access(
                user_tg_id, UserAccCode.BOT.value, expired_delta_days
            )
            if resp_2 == ReturnCode.SUCCESS:
                await call.message.edit_text(
                    f"🔄 Обновил доступ для {user_tg_id} "
                    f"на {expired_delta_days} дней 📅",
                    reply_markup=all_access_request_btn(user_tg_id),
                )
                await send_success_bot_sub_user(user_tg_id, expired_delta_days)
            else:
                raise BaseException(
                    f"BAD TRY UPDATE ACCESS FOR USER {user_tg_id}"
                )
        else:
            raise BaseException(f"BAD TRY ADD ACCESS FOR USER {user_tg_id}")
    except Exception as e:
        mess = f"❌ Ошибка добавления доступа для {user_tg_id}"
        logger.error(e)
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=all_access_request_btn(user_tg_id),
        )


async def all_bot_access_requests(call: CallbackQuery, user_tg_id: int):
    access_requests = await dbm.get_access_requests(
        UserAccCode.BOT.value, limit=3
    )
    if access_requests:
        mess = ""
        for idx, req in enumerate(access_requests):
            user_tg_id = req[0]
            user_tag = req[1]
            sys_inserted_dttm: datetime = req[3]
            inserted_dttm = sys_inserted_dttm.strftime("%Y/%m/%d %H:%M:%S")
            mess += (
                f"{idx+1}. @{user_tag} ({user_tg_id}):\n"
                f"Дата форм. заявки: {inserted_dttm}\n\n"
            )

        await call.message.edit_text(
            "📋 Показываю до трех активных заявок: \n" + mess,
            reply_markup=access_requests_kb(
                user_tg_id, access_requests
            ).as_markup(),
        )
    else:
        await call.message.edit_text(
            "📭 Тут ничего нет...",
            reply_markup=all_access_request_btn(user_tg_id),
        )


async def all_conf_pay_requests(call: CallbackQuery, user_tg_id: int):
    payed_orders = await dbm.get_payed_orders(limit=3)
    if payed_orders:
        mess = ""
        for idx, ord in enumerate(payed_orders):
            user_tg_id = ord[0]
            user_tag = ord[1]
            order_data: dict = ord[3]
            sys_updated_dttm: datetime = ord[4]

            config_name = order_data.get("config_name", "")
            updated_dttm = sys_updated_dttm.strftime("%Y/%m/%d %H:%M:%S")

            mess += (
                f"{idx+1}. @{user_tag} ({user_tg_id}):\n"
                f"Конфиг: {config_name}\n"
                f"Дата обн. заявки: {updated_dttm}\n\n"
            )

        await call.message.edit_text(
            "📋 Показываю до трех активных заявок: \n" + mess,
            reply_markup=conf_pay_requests_btn(user_tg_id, payed_orders),
        )
    else:
        await call.message.edit_text(
            "📭 Тут ничего нет...",
            reply_markup=all_conf_pay_requests_btn(user_tg_id),
        )


async def accept_conf_pay_request(
    call: CallbackQuery, user_tg_id: int, user_config_name: str
):
    try:
        expired_delta_days = settings.CONF_PAY_EXPIRED_DELTA_DAYS
        upd_resp = await VlessClientApi().update_client_expired_time(
            user_config_name,
            datetime.now() + timedelta(expired_delta_days),
        )
        if upd_resp:
            resp = await dbm.close_payed_order(
                user_tg_id,
                user_config_name,
                expired_delta_days=expired_delta_days,
            )
            if resp == ReturnCode.SUCCESS:
                await call.message.edit_text(
                    f"✅ Обновил статус заказа для {user_tg_id}, "
                    f"{user_config_name} "
                    f"и продлил доступ сервиса "
                    f"на {expired_delta_days} дней 📅",
                    reply_markup=admin_menu_kb(user_tg_id),
                )
                await bot.send_message(
                    user_tg_id,
                    f"👋 Привет!\nТебе подтвердили оплату для "
                    f"конфига {user_config_name}! 🎉\n"
                    f"Конфиг продлен на {expired_delta_days} дней\n"
                    "Открой меню: /menu и выбери необходимый раздел "
                    f"с подключениями",
                )
            else:
                raise BaseException(
                    f"BAD TRY TO AСCEPT SERVICE ACCESS TO {user_tg_id}"
                )
        else:
            raise BaseException(
                f"BAD TRY TO ACСEPT SERVICE ACCESS TO {user_tg_id} ON 3XUI"
            )
    except Exception as e:
        logger.error(e)
        mess = (
            f"❌ Ошибка добавления доступа для"
            f"{user_tg_id} {user_config_name}"
        )
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=admin_menu_kb(user_tg_id),
        )


async def decline_conf_pay_request(
    call: CallbackQuery, user_tg_id: int, user_config_name: str
):
    try:
        resp = await dbm.update_order_status(
            user_tg_id,
            user_config_name,
            OrderStatus.PAYED.value,
            OrderStatus.NEW.value,
        )
        if resp == ReturnCode.SUCCESS:
            await call.message.edit_text(
                f"❌ Вернул заказ в состояние {OrderStatus.NEW.value} для "
                f"{user_tg_id} {user_config_name}",
                reply_markup=admin_menu_kb(user_tg_id),
            )
            await bot.send_message(
                user_tg_id,
                f"👋 Привет!\nТвоя оплата для конфига {user_config_name} "
                f"была отклонена! ❌",
            )
        else:
            raise BaseException(
                f"BAD TRY TO DECLINE SERVICE ACCESS TO {user_tg_id}"
            )

    except Exception as e:
        logger.error(e)
        mess = (
            f"❌ Ошибка отклонить заказ в "
            f"состояние {OrderStatus.NEW.value} для "
            f"{user_tg_id} {user_config_name}"
        )
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=admin_menu_kb(user_tg_id),
        )


async def admin_cb_cmd(call: CallbackQuery):
    try:
        call_data = call.data.split(":")

        call_tag = call_data[0]
        user_tg_id = int(call_data[1])

        user_config_name = ""
        if len(call_data) > 2:
            user_config_name = call_data[2]

        db_user = await dbm.get_user(user_tg_id)
        if db_user.admin_flg:
            match call_tag:
                case "admin_all_ar_btn":
                    await all_bot_access_requests(call, user_tg_id)

                case "admin_all_conf_pay_btn":
                    await all_conf_pay_requests(call, user_tg_id)

                case "admin_menu_back_btn":
                    await call.message.edit_text(
                        "Админ, вот меню для тебя 📋",
                        reply_markup=admin_menu_kb(user_tg_id),
                    )

        match call_tag:
            case "admin_ar_acpt_btn":
                await accept_bot_access_request(call, user_tg_id)

            case "admin_ar_decl_btn":
                # TODO make decline access request button
                pass

            case "admin_conf_pay_acpt_btn":
                await accept_conf_pay_request(
                    call, user_tg_id, user_config_name
                )

            case "admin_conf_pay_decl_btn":
                await decline_conf_pay_request(
                    call, user_tg_id, user_config_name
                )

    except Exception as e:
        logger.error(f"{e}")
    finally:
        await call.answer()
