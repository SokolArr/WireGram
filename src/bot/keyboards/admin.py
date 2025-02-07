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


def access_requests_kb(requests: list[UserAccReqStruct]):

    builder = InlineKeyboardBuilder()
    for request in requests:
        user_id = request[0]
        builder.row(
            InlineKeyboardButton(
                text=f"✅ {user_id}",
                callback_data=(f"admin_ar_acpt_btn:{user_id}"),
            ),
            InlineKeyboardButton(
                text=f"⛔️ {user_id}",
                callback_data=(f"admin_ar_decl_btn:{user_id}"),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Все заявки к боту", callback_data=(f"admin_all_ar_btn:0")
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админ-меню", callback_data=f"admin_menu_back_btn:0"
        )
    )

    builder
    return builder


def conf_pay_request_kb(user_tg_id: int, config_name: str):
    kb = [
        [
            InlineKeyboardButton(
                text="✅ Принять оплату",
                callback_data=f"admin_conf_pay_acpt_btn:{user_tg_id}:{config_name}",
            )
        ],
        [
            InlineKeyboardButton(
                text="⛔️ Отклонить оплату",
                callback_data=f"admin_conf_pay_decl_btn:{user_tg_id}:{config_name}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def conf_pay_requests_btn(orders: tuple):
    """
    user_tg_id,
    order_status,
    order_data,
    sys_updated_dttm
    """

    builder = InlineKeyboardBuilder()

    for order in orders:
        user_tg_id = order[0]
        config_name = order[2]["config_name"]

        builder.row(
            InlineKeyboardButton(
                text=f"✅ {user_tg_id} {config_name}",
                callback_data=(
                    f"admin_conf_pay_acpt_btn:{user_tg_id}:{config_name}"
                ),
            ),
            InlineKeyboardButton(
                text=f"⛔️ {user_tg_id} {config_name}",
                callback_data=(
                    f"admin_conf_pay_decl_btn:{user_tg_id}:{config_name}"
                ),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Все заявки на оплату",
            callback_data=f"admin_all_conf_pay_btn:0",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админ-меню", callback_data=f"admin_menu_back_btn:0"
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
