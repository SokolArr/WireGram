from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from modules.db.models import UserServConfStruct

def new_service_kb(user_tg_id: int):
    kb = [
        [InlineKeyboardButton(text="✅ Создать конфиг", callback_data=f'serv_get_new_btn:{user_tg_id}:no_conf')],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_back_btn:{user_tg_id}:no_conf')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def services_kb(user_tg_id: int, user_configs: list[UserServConfStruct]):
    builder = InlineKeyboardBuilder()
    
    for idx, config in enumerate(user_configs):
        builder.row(InlineKeyboardButton(text=f"{idx+1}. {config.config_name}", callback_data=f'serv_chosse_btn:{user_tg_id}:{config.config_name}'))
        
    if len(user_configs) <= 2:
        builder.row(InlineKeyboardButton(text="✅ Создать конфиг", callback_data=f'serv_get_new_btn:{user_tg_id}:no_conf')) 
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_back_btn:{user_tg_id}:no_conf')
    )
    return builder.as_markup()

def service_del_view(user_tg_id: int):
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_service_btn:{user_tg_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def new_order_view(user_tg_id: int, config_name: str):
    kb = [
        [InlineKeyboardButton(text="💵 Оплатил!", callback_data=f'serv_payed_btn:{user_tg_id}:{config_name}')],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_service_btn:{user_tg_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def new_conf_view(user_tg_id: int, config_name: str):
    kb = [
        [InlineKeyboardButton(text=f"{config_name}", callback_data=f'serv_chosse_btn:{user_tg_id}:{config_name}')],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_service_btn:{user_tg_id}:{config_name}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def service_back_btn(user_tg_id: int, config_name: str):
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f'serv_chosse_btn:{user_tg_id}:{config_name}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def actions_conf_kb(user_tg_id: int, config_name: str, is_renew_req: bool = False, is_pay_req: bool = False):
    kb = []
    if is_renew_req:
        kb.append([InlineKeyboardButton(text="✅ Продлить доступ", callback_data=f'serv_renew_btn:{user_tg_id}:{config_name}')])
    if is_pay_req:
        kb.append([InlineKeyboardButton(text="💵 Оплатил!", callback_data=f'serv_payed_btn:{user_tg_id}:{config_name}')])
    
    kb.append([InlineKeyboardButton(text="🔗 Ссылка на подключение", callback_data=f'serv_get_path_btn:{user_tg_id}:{config_name}')])
    kb.append([InlineKeyboardButton(text="⛔️ Удалить конфиг", callback_data=f'serv_del_conf_btn:{user_tg_id}:{config_name}')])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f'menu_service_btn:{user_tg_id}:no_conf')])
    return InlineKeyboardMarkup(inline_keyboard=kb)

