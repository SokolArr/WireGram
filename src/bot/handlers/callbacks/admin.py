import logging
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
from settings import settings

dbm = DbManager()
bot = Bot(
    settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
logger = logging.getLogger(__name__)


async def admin_cb_cmd(call: CallbackQuery):
    """
    Handle callback queries for admin actions.

    Args:
        call (CallbackQuery): The callback query from the admin.
    """
    try:
        call_data = call.data.split(":")
        call_tag = call_data[0]
        user_tg_id = int(call_data[1])
        user_config_name = ""
        if len(call_data) > 2:
            user_config_name = call_data[2]

        match call_tag:
            case "admin_ar_acpt_btn":
                try:
                    resp = await dbm.add_access(user_tg_id, "BOT", 365)
                    if resp == ReturnCode.SUCCESS:
                        await call.message.edit_text(
                            f"✅ Добавил доступ для {user_tg_id}",
                            reply_markup=all_access_request_btn(user_tg_id),
                        )
                        await bot.send_message(
                            user_tg_id,
                            "👋 Привет! Тебе одобрили подписку на бота 🎉\n"
                            "Используй /menu, чтобы узнать что можно сделать",
                        )
                    elif resp == ReturnCode.UNIQUE_VIOLATION:
                        resp_2 = await dbm.update_access(
                            user_tg_id, "BOT", 365
                        )
                        if resp_2 == ReturnCode.SUCCESS:
                            await call.message.edit_text(
                                f"🔄 Обновил доступ для {user_tg_id}",
                                reply_markup=all_access_request_btn(
                                    user_tg_id
                                ),
                            )
                            await bot.send_message(
                                user_tg_id,
                                "👋 Привет! Тебе продлили подписку на бота 🎉\n"
                                "Используй /menu, чтобы узнать что можно сделать",
                            )
                        else:
                            raise Exception
                    else:
                        raise Exception
                except Exception:
                    await call.message.edit_text(
                        f"❌ Ошибка добавления доступа для {user_tg_id}",
                        reply_markup=all_access_request_btn(user_tg_id),
                    )

            case "admin_ar_decl_btn":
                pass

            case "admin_all_ar_btn":
                access_requests = await dbm.get_access_requests("BOT", limit=3)
                if access_requests:
                    await call.message.edit_text(
                        "📋 Вот первые три заявки:",
                        reply_markup=access_requests_kb(
                            access_requests
                        ).as_markup(),
                    )
                else:
                    await call.message.edit_text(
                        "📭 Тут пусто...",
                        reply_markup=all_access_request_btn(user_tg_id),
                    )

            case "admin_conf_pay_acpt_btn":
                expired_delta_days = 30
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
                            f"✅ Обновил статус заказа для {user_tg_id} {user_config_name} "
                            "и продлил доступ сервиса на 30 дней 📅",
                            reply_markup=admin_menu_kb(user_tg_id),
                        )
                        await bot.send_message(
                            user_tg_id,
                            f"👋 Привет!\nТебе подтвердили оплату для конфига {user_config_name}! 🎉\n"
                            "Открой меню: /menu и выбери необходимый раздел с подключениями",
                        )
                    else:
                        await call.message.edit_text(
                            f"❌ Ошибка добавления доступа для {user_tg_id} {user_config_name}",
                            reply_markup=admin_menu_kb(user_tg_id),
                        )
                        logger.error(
                            f"BAD TRY TO ACEPT SERVICE ACCESS TO {user_tg_id}"
                        )
                else:
                    await call.message.edit_text(
                        f"❌ Ошибка добавления доступа для {user_tg_id} {user_config_name} на 3xui",
                        reply_markup=admin_menu_kb(user_tg_id),
                    )
                    logger.error(
                        f"BAD TRY TO ACEPT SERVICE ACCESS TO {user_tg_id} ON 3XUI"
                    )

            case "admin_conf_pay_decl_btn":
                resp = await dbm.update_order_status(
                    user_tg_id, user_config_name, "PAYED", "NEW"
                )
                if resp == ReturnCode.SUCCESS:
                    await call.message.edit_text(
                        f"❌ Отклонил заказ для {user_tg_id} {user_config_name} в состояние NEW",
                        reply_markup=admin_menu_kb(user_tg_id),
                    )
                    await bot.send_message(
                        user_tg_id,
                        f"👋 Привет!\nТвоя оплата для конфига {user_config_name} была отклонена! ❌",
                    )
                else:
                    await call.message.edit_text(
                        f"❌ Ошибка отклонить заказ для {user_tg_id} {user_config_name} в состояние NEW",
                        reply_markup=admin_menu_kb(user_tg_id),
                    )
                    logger.error(
                        f"BAD TRY TO DECLINE SERVICE ACCESS TO {user_tg_id}"
                    )

            case "admin_all_conf_pay_btn":
                payed_orders = await dbm.get_payed_orders(limit=3)
                if payed_orders:
                    await call.message.edit_text(
                        "📋 Вот первые три заявки:",
                        reply_markup=conf_pay_requests_btn(payed_orders),
                    )
                else:
                    await call.message.edit_text(
                        "📭 Тут пусто...",
                        reply_markup=all_conf_pay_requests_btn(user_tg_id),
                    )

            case "admin_menu_back_btn":
                await call.message.edit_text(
                    "Вот меню для тебя", reply_markup=admin_menu_kb(user_tg_id)
                )

    except Exception as e:
        logger.error(f"{e}")
    finally:
        await call.answer()
