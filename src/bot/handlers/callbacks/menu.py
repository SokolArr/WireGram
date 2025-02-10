from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import html, Bot
from datetime import datetime

from ...keyboards.menu import menu_kb
from ...keyboards.account import account_kb
from ...keyboards.service import new_service_kb, services_kb
from modules.db import DbManager
from modules.db.models import UserAccCode, OrderStatus, get_order_nm_str
from settings import settings
from logger import MainLogger, get_error_timestamp

dbm = DbManager()
bot = Bot(
    settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
logger = MainLogger(__name__).get()


async def user_account(call: CallbackQuery, user_tg_id: int):
    try:
        db_user = await dbm.get_user(user_tg_id)
        profile_str = (
            f"\n👤 {html.bold("Профиль:")}"
            f"\n\t- Имя: {db_user.user_name}"
            f"\n\t- TG ID: {html.code(str(db_user.user_tg_id))}\n"
        )
        bot_access = await dbm.get_access(user_tg_id, UserAccCode.BOT.value)
        access_valid_to = bot_access.valid_to_dttm.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        bot_access_str = (
            f"\n🔑 {html.bold("Доступ к боту:")}"
            "\n\t- Статус: Активен ✅"
            f"\n\t- Действует до: {access_valid_to}\n"
        )
        user_orders = await dbm.get_oders_hist(user_tg_id)
        order_mess = ""
        if user_orders:
            order_mess += f"\n📦 {html.bold("История заказов:")}"
            order_mess += html.italic(
                "\n(cтатусы: 🆕 сформирован -> 💵 оплачен -> ✅ завершен)"
            )
            for idx, order in enumerate(user_orders):
                order_id = get_order_nm_str(order)
                order_upd_dt_str = order.sys_updated_dttm.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if order.order_status == OrderStatus.NEW.value:
                    status = "🆕 сформирован"
                elif order.order_status == OrderStatus.PAYED.value:
                    status = "💵 оплачен"
                elif order.order_status == OrderStatus.CLOSED.value:
                    status = "✅ завершен"
                order_mess += (
                    f"\n\t{idx + 1}. Заказ {html.code(order_id)} "
                    f"(статус: {status}, время: {order_upd_dt_str})"
                )

            order_mess += "\n"

        help_str = (
            f"\n📞 {html.bold("Поддержка:")}"
            "\n\t- Команда: /help"
            f"\n\t- Чат: {settings.TG_HELP_CHAT_LINK}\n"
        )

        user_configs = await dbm.get_service_configs(user_tg_id)
        conf_mess = ""
        if user_configs:
            conf_mess += f"\n🛠️ {html.bold("Конфигурации:")}"
            for idx, conf in enumerate(user_configs):
                conf_mess += f"\n\t{idx + 1}. {html.code(conf.config_name)}"
            conf_mess += "\n"

        mess = (
            html.bold("📂 Личный кабинет\n")
            + profile_str
            + bot_access_str
            + conf_mess
            + order_mess
            + help_str
            + f"\n{html.italic(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}"
        )
        await call.message.edit_text(
            mess,
            reply_markup=account_kb(user_tg_id),
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Не смог получить данные по личному кабинету {user_tg_id}"
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=menu_kb(user_tg_id),
        )


async def user_services(call: CallbackQuery, user_tg_id: int):
    try:
        pre_mess = (
            f"{html.bold("🌎 Сервисы и конфигурации\n\nℹ️ О разделе")}\n"
            + (
                "- Это раздел сервисов и конфигураций для них. "
                "Hа данный момент доступны"
                " конфигурации только на протоколе подключения 'VLESS' \n"
            )
        )
        user_configs = await dbm.get_service_configs(user_tg_id)
        if user_configs:
            conf_mess = "\n"
            for idx, conf in enumerate(user_configs):
                conf_valid_to_dttm = conf.valid_to_dttm

                if datetime.now() > conf_valid_to_dttm:
                    active_place_holder = "⛔️ доступ закончился"
                else:
                    active_place_holder = "✅ активна до"

                conf_valid_to_dttm_str = conf_valid_to_dttm.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                conf_mess += (
                    f"\t{idx + 1}. {html.code(conf.config_name)} "
                    f"({active_place_holder} {conf_valid_to_dttm_str})\n"
                )
            pre_mess_2 = (
                "- Продлить доступ или получить ссылку для "
                "подключения можно с помощью соответствующей кнопки ниже\n"
            )
            used_configs = f"{len(user_configs)}/{settings.MAX_CONF_PER_USER}"
            mess = (
                pre_mess
                + pre_mess_2
                + html.bold(f"\n🛠️ Конфигурации ({used_configs})")
                + conf_mess
            )
            await call.message.edit_text(
                mess,
                reply_markup=services_kb(user_tg_id, user_configs),
            )
        else:
            used_configs = f"0/{settings.MAX_CONF_PER_USER}"
            mess = (
                html.bold(f"\n🛠️ Конфигурации ({used_configs})")
                + "\n- ⚠️ Не нашел твоих конфигураций. "
                "Но ты можешь создать новый 🙂"
            )
            await call.message.edit_text(
                pre_mess + mess,
                reply_markup=new_service_kb(user_tg_id),
            )
    except Exception as e:
        logger.error(e)
        mess = f"❌ Не смог получить данные по сервисам {user_tg_id}"
        await call.message.edit_text(
            mess + f"{get_error_timestamp(logger)}",
            reply_markup=menu_kb(user_tg_id),
        )


async def menu_cb_cmd(call: CallbackQuery):
    try:
        call_tag = call.data.split(":")[0]
        user_tg_id = int(call.data.split(":")[1])

        match call_tag:
            case "menu_ua_btn":
                await user_account(call, user_tg_id)

            case "menu_service_btn":
                await user_services(call, user_tg_id)

            case "menu_pref_btn":
                pass

            case "menu_back_btn":
                await call.message.edit_text(
                    html.bold("📋 Меню")
                    + "\n\n"
                    + html.bold("📂 Личный кабинет")
                    + "\nЗдесь ты можешь посмотреть свой "
                    "профиль, статус доступа к боту, "
                    "историю заказов и конфигурации.\n\n"
                    + html.bold("🌎 Сервисы и конфигурации")
                    + "\nУправляй своими "
                    "конфигурациями для подключения. "
                    "Создавай новые или редактируй существующие.",
                    reply_markup=menu_kb(user_tg_id),
                )

    except Exception as e:
        logger.error(f"{e}")
    finally:
        await call.answer()
