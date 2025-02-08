from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.db.models import UserAccReqStruct


def admin_menu_kb(user_tg_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="🔤 Все заявки к боту",
                callback_data=f"admin_all_ar_btn:{user_tg_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="💵 Все заявки на оплату",
                callback_data=f"admin_all_conf_pay_btn:{user_tg_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def access_request_kb(user_tg_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"admin_ar_acpt_btn:{user_tg_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="⛔️ Отклонить",
                callback_data=f"admin_ar_decl_btn:{user_tg_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def all_access_request_btn(user_tg_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="🔤 Все заявки к боту",
                callback_data=f"admin_all_ar_btn:{user_tg_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в админ-меню",
                callback_data=f"admin_menu_back_btn:{user_tg_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def access_requests_kb(user_tg_id: int, requests: list[UserAccReqStruct]):

    builder = InlineKeyboardBuilder()
    for idx, request in enumerate(requests):
        user_id = request[0]
        builder.row(
            InlineKeyboardButton(
                text=f"✅ {idx+1}. {user_id}",
                callback_data=(f"admin_ar_acpt_btn:{user_id}"),
            ),
            InlineKeyboardButton(
                text=f"⛔️ {idx+1}. {user_id}",
                callback_data=(f"admin_ar_decl_btn:{user_id}"),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Все заявки к боту",
            callback_data=(f"admin_all_ar_btn:{user_tg_id}"),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админ-меню",
            callback_data=f"admin_menu_back_btn:{user_tg_id}",
        )
    )

    builder
    return builder


def conf_pay_request_kb(user_tg_id: int, config_name: str):
    kb = [
        [
            InlineKeyboardButton(
                text="✅ Принять оплату",
                callback_data=(
                    f"admin_conf_pay_acpt_btn:{user_tg_id}:{config_name}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text="⛔️ Отклонить оплату",
                callback_data=(
                    f"admin_conf_pay_decl_btn:{user_tg_id}:{config_name}"
                ),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def conf_pay_requests_btn(user_tg_id: int, orders: tuple):
    """
    [(u.user_tg_id,
      u.user_tag,
      o.order_status,
      o.order_data,
      o.sys_updated_dttm),
    ]
    """

    builder = InlineKeyboardBuilder()

    for idx, order in enumerate(orders):
        user_tg_id = order[0]
        order_data: dict = order[3]
        config_name = order_data.get("config_name", "")

        builder.row(
            InlineKeyboardButton(
                text=f"✅ {idx+1}. {config_name}",
                callback_data=(
                    f"admin_conf_pay_acpt_btn:{user_tg_id}:{config_name}"
                ),
            ),
            InlineKeyboardButton(
                text=f"⛔️ {idx+1}. {config_name}",
                callback_data=(
                    f"admin_conf_pay_decl_btn:{user_tg_id}:{config_name}"
                ),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Все заявки на оплату",
            callback_data=f"admin_all_conf_pay_btn:{user_tg_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админ-меню",
            callback_data=f"admin_menu_back_btn:{user_tg_id}",
        )
    )
    return builder.as_markup()


def all_conf_pay_requests_btn(user_tg_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="🔤 Все заявки на оплату",
                callback_data=f"admin_all_conf_pay_btn:{user_tg_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в админ-меню",
                callback_data=f"admin_menu_back_btn:{user_tg_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
