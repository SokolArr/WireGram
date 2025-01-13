import asyncio, logging, sys
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F

from models.user import User, UserDataSchema, OrderResponse
from models.admin import Admin
from modules.db_api.manager import DbManager
from modules.db_api.models import UserStruct, UserOrderStruct
from settings import settings

BOT_STARTED_DTTM = datetime.now(tz=timezone.utc)
DTTM_FORMAT = '%Y-%m-%d %H:%M:%S'
DT_FORMAT = '%Y-%m-%d'

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dbm = DbManager()
dp = Dispatcher()

# Helpers&Utils 
async def error_message(message: Message, exeption:str, err_code:int):
    if err_code == 1:
        err_mess = html.pre(f"Возникла критическая ошибка: {datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"+"ERR"+str(err_code))
        logging.error(f'tg_error_message:{err_mess};exeption:{exeption}')
        await message.answer(f"⚠️ Возникла критическая ошибка!\n\n- Отправь письмо с текстом "+html.bold('из следующего cообщения')
                             + " - на почту yamcbot@gmail.com.\n" +
                             "- Если проблема не исправлена, то напиши, пожалуйста, в группу: https://t.me/c/2218172872/16")
        await message.answer(err_mess)           
         
# Message data 
def get_requests_message(request, schema: list, max_length: int=1024):
    mess = ''
    for row_id in range(len(request)):
        mess += f'{html.bold(str(row_id + 1))}. '
        for col_id in range(len(request[row_id])):
            mess += (f'{schema[col_id]}: '+ 
                     f'{"@" if schema[col_id]=="user_tag" and request[row_id][col_id] else ""}{request[row_id][col_id]}' 
                     + ', ')
        mess += '\n\n'
    return mess[:max_length]
    
async def send_request_message_to_admins(user_db_data: UserStruct, access_name: str, admins: list = None):
    if admins == None:
        admins = await Admin().get_admins_tg_code()
    for admin in admins:
        await bot.send_message(int(admin), f'{html.bold("ВНИМАНИЕ! ЛИЧНОЕ УВЕДОМЛЕНИЕ АДМИНИСТРАТОРА!")}\n\n'+
                               f'Пользователь {user_db_data.user_tg_code}, @{user_db_data.user_tag} запросил доступ к {access_name}!')

async def send_payed_message_to_admins(user_db_data: UserStruct, admins: list = None):
    if admins == None:
        admins = await Admin().get_admins_tg_code()
    for admin in admins:
        await bot.send_message(int(admin), f'{html.bold("ВНИМАНИЕ! ЛИЧНОЕ УВЕДОМЛЕНИЕ АДМИНИСТРАТОРА!")}\n\n'+
                               f'Пользователь {user_db_data.user_tg_code}, @{user_db_data.user_tag} оплатил заказ!\n'+
                               f'Сформирован автоматический запрос на доступ к VPN для пользователя.\n' +
                               f'Вызвать админ-меню /admin')


# Keyboards    
def get_menu_keyboard_by_user_data(user_data: UserStruct):
    user_tg_code = user_data.user_tg_code
    admin_flg = user_data.admin_flg
    
    ikb = [[InlineKeyboardButton(text="📊 Проверить остатки и баланс", callback_data=f'menu_btn_get_all_status__{user_data.user_tg_code}')],
        [InlineKeyboardButton(text="📄 Конфиг для подключения", callback_data=f'menu_btn_get_conf__{user_data.user_tg_code}')],
        [InlineKeyboardButton(text="✅ Продлить доступ", callback_data=f'menu_btn_renew_vpn_access__{user_data.user_tg_code}')]]
    if admin_flg:
        ikb.append([InlineKeyboardButton(text="⚠️ АДМИН-МЕНЮ", callback_data=f'admin_btn_secret_menu__{user_data.user_tg_code}')])
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_renew_kb_by_user_data(user_data: UserStruct):    
    ikb = [[InlineKeyboardButton(text="Направить запрос", callback_data=f'menu_btn_send_order__{user_data.user_tg_code}')],
        [InlineKeyboardButton(text="Я оплатил!", callback_data=f'menu_btn_allready_payed__{user_data.user_tg_code}')],
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data=f'menu_btn_back_menu__{user_data.user_tg_code}')]]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_to_pay_kb_by_user_data(user_data: UserStruct):    
    ikb = [[InlineKeyboardButton(text="Я оплатил!", callback_data=f'menu_btn_allready_payed__{user_data.user_tg_code}')],
            [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data=f'menu_btn_back_menu__{user_data.user_tg_code}')]]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_admin_menu_keyboard(user_data: UserStruct):
    user_tg_code = user_data.user_tg_code
    admin_flg = user_data.admin_flg
    ikb = []
    if admin_flg:
        ikb = ([
            [InlineKeyboardButton(text="Запросы BOT", 
                                callback_data=('admin_btn_req_bot__' + str(user_tg_code))
                                )],
            [InlineKeyboardButton(text="Запросы VPN", 
                                callback_data=('admin_btn_req_vpn__' + str(user_tg_code))
                                )],
            [InlineKeyboardButton(text="🔤 Открыть пользовательское меню", 
                                    callback_data=('menu_btn_back_menu__'+str(user_tg_code))
                                    )]
        ])
    else:
        ikb = [[InlineKeyboardButton(text="Нет доступа", 
                                    callback_data=('admin_btn_noaccess__'+str(user_tg_code))
                                    )]]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_admin_menu_back_btn(user_data: UserStruct):
    user_tg_code = user_data.user_tg_code
    ikb = [
        [InlineKeyboardButton(text="⬅️ Вернуться в админ-меню", 
                                callback_data=('admin_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_admin_choose_keyboard(user_data: UserStruct, data: list[tuple]):
    user_tg_code = user_data.user_tg_code
    new_data = []
    for row_id in range(len(data)):
        new_data.append(
                {
                    'row_id': row_id,
                    'user_tg_code': data[row_id][0],
                    'req_access_name': data[row_id][2]
                })
    builder = InlineKeyboardBuilder()
    for el in new_data:
        builder.row(InlineKeyboardButton(text=f" ✅ Принять #{el['row_id'] + 1} - {el['user_tg_code']}", 
                                            callback_data=(f'admin_btn_ch_a' + '__' + 
                                                            user_tg_code + '__' + 
                                                            el['user_tg_code'] + '__' + el['req_access_name']
                                            ))
                   ,InlineKeyboardButton(text=f"⛔️ Отклонить #{el['row_id'] + 1} - {el['user_tg_code']}", 
                                            callback_data=(f'admin_btn_ch_d' + '__' + 
                                                            user_tg_code + '__' + 
                                                            el['user_tg_code'] +'__' + el['req_access_name']
                                            ))
        )
    builder.row(
        InlineKeyboardButton(text="⬅️ Вернуться в админ-меню", 
                                callback_data=(f'admin_btn_back_menu'+ '__' + user_tg_code)
                                )
    )
    return builder

def get_menu_back_renew_keyboard(user_data: UserStruct):
    user_tg_code = user_data.user_tg_code
    ikb = [
        [InlineKeyboardButton(text="✅ Продлить доступ", 
                              callback_data=('menu_btn_renew_vpn_access__' + str(user_tg_code))
                             )],
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", 
                                callback_data=('menu_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_back_btn(user_data: UserStruct):
    user_tg_code = user_data.user_tg_code
    ikb = [
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", 
                                callback_data=('menu_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_btn(user_data: UserStruct):
    user_tg_code = user_data.user_tg_code
    ikb = [
        [InlineKeyboardButton(text="🔤 Открыть меню", 
                                callback_data=('menu_btn_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

# Buttons handlers  
@dp.callback_query(F.data.startswith("menu_btn"))
async def menu_btn_handler(call: types.CallbackQuery):
    if call.message.date > BOT_STARTED_DTTM:
        try:
            user_data: UserDataSchema = await User.validate_bot_access(str(call.from_user.id))
            call_data = call.data.split('__') # <button_tag>__<user_tg_code>
            button_tag = call_data[0]
            
            if user_data.user_db_data:
                if user_data.user_bot_access_data:
                    if user_data.user_bot_access_data.access:
                        
                        if button_tag == 'menu_btn_get_conf':
                            if user_data.user_vpn_access_data:
                                if user_data.user_vpn_access_data.access:
                                    await call.message.edit_text("🔎 Ушел искать...")
                                    try:
                                        vless_conf = await User(user_data.user_db_data).get_or_create_vless_config()
                                        await call.message.edit_text("Вот твой конфиг для подключения.\nCкопируй его нажатием на этот блок:\n"+html.pre(vless_conf))
                                        await call.message.answer("Вставь в приложение из буфера обмена.\nПриятного пользования 😃", reply_markup=get_menu_back_btn(user_data.user_db_data))
                                    except Exception as e:
                                        await error_message(call.message, e, 1)
                                else:
                                    await call.message.edit_text("⚠️ У тебя нет активной подписки", reply_markup=get_menu_back_renew_keyboard(user_data.user_db_data))
                            else:
                                await call.message.edit_text("⚠️ У тебя нет активной подписки", reply_markup=get_menu_back_renew_keyboard(user_data.user_db_data))
                        
                        elif button_tag == 'menu_btn_get_all_status':
                            vpn_access_mess = f"{html.bold('VPN: (')}"
                            bot_access_mess = f"{html.bold('БОТ: (✅):')}"
                            bot_access_mess += f" доступен с {html.bold(user_data.user_bot_access_data.dates[0].strftime(DT_FORMAT))} по {html.bold(user_data.user_bot_access_data.dates[1].strftime(DT_FORMAT))}\n"
                            
                            if user_data.user_vpn_access_data:
                                vpn_access_mess += f"{'✅):' if user_data.user_vpn_access_data.access else '⛔️): был'} VPN"
                                vpn_access_mess += f" доступен с {html.bold(user_data.user_vpn_access_data.dates[0].strftime(DT_FORMAT))} по {html.bold(user_data.user_vpn_access_data.dates[1].strftime(DT_FORMAT))}\n"
                            else:
                                vpn_access_mess += f"⛔️): нет доступа"
                                
                            order_data: UserOrderStruct = await User(user_data.user_db_data).get_order()
                        
                            vpn_request_mess = html.bold(f'VPN: ')
                            order_status_mess = html.bold(f'Оплата: ')
                            vpn_request_data = await User(user_data.user_db_data).get_vpn_request_access()
                            
                            if vpn_request_data:
                                vpn_request_mess += f'Есть запрос на подписку VPN от {html.bold(vpn_request_data.sys_processed_dttm.strftime(DTTM_FORMAT))}'
                            else:
                                vpn_request_mess += f'Нет активного запроса на подписку VPN'
                                
                            if order_data:
                                order_status = ''
                                if order_data.order_status == 'NEW': order_status = 'cформирован'
                                elif order_data.order_status == 'PAYED': order_status = 'оплачен'
                                elif order_data.order_status == 'CLOSED': order_status = 'завершен'   
                                order_status_mess += (f'Заказ в статусе {html.bold(order_status)}' 
                                                      + f' с {html.bold(order_data.sys_processed_dttm.strftime(DTTM_FORMAT))}')
                            else:
                                order_status_mess += 'Нет данных по заказу'
                                
                            mess = (html.bold('Подписки:\n')+ 
                                    bot_access_mess + 
                                    vpn_access_mess +
                                    html.bold('\nЗапросы:\n') +
                                    vpn_request_mess + '\n' +
                                    order_status_mess)
                            await call.message.edit_text(f"{mess}",reply_markup=get_menu_back_btn(user_data.user_db_data))
                            
                        elif button_tag == 'menu_btn_send_order':
                            resp = await User(user_data.user_db_data).make_order()
                            if resp == OrderResponse.SUCCESS:
                                await call.message.edit_text(f"Заказ сформирован",reply_markup=get_menu_back_btn(user_data.user_db_data))
                                await send_request_message_to_admins(user_data.user_db_data, 'VPN')
                            elif resp == OrderResponse.NEW_ORDER_EXIST:
                                await call.message.edit_text(f"Заказ надо оплатить",reply_markup=get_to_pay_kb_by_user_data(user_data.user_db_data))
                            elif resp == OrderResponse.PAYED_ORDER_EXIST:
                                await call.message.edit_text(f"Заказ в обработке...",reply_markup=get_menu_back_btn(user_data.user_db_data))
                            elif resp == OrderResponse.BAD_TRY:
                                await call.message.edit_text(f"Ошибка в обработке заказа",reply_markup=get_menu_back_btn(user_data.user_db_data))
                            
                        elif button_tag == 'menu_btn_allready_payed':
                            resp = await User(user_data.user_db_data).make_new_order_pay()
                            if resp == OrderResponse.SUCCESS:
                                await call.message.edit_text(f"Отлично! Обрабатываю...",reply_markup=get_menu_back_btn(user_data.user_db_data))
                                await send_payed_message_to_admins(user_data.user_db_data)
                                await User(user_data.user_db_data).make_new_vpn_request_access()
                            elif resp == OrderResponse.NEW_ORDER_NF:
                                await call.message.edit_text(f"Не смог найти твой заказ",reply_markup=get_menu_back_btn(user_data.user_db_data))
                            elif resp == OrderResponse.PAYED_ORDER_EXIST:
                                await call.message.edit_text(f"Заказ в обработке...",reply_markup=get_menu_back_btn(user_data.user_db_data))
                            elif resp == OrderResponse.BAD_TRY:
                                await call.message.edit_text(f"Ошибка в обработке заказа",reply_markup=get_menu_back_btn(user_data.user_db_data))
                            
                        elif button_tag == 'menu_btn_renew_vpn_access':
                            await call.message.edit_reply_markup()
                            await call.message.edit_text("Выбери ",reply_markup=get_renew_kb_by_user_data(user_data.user_db_data))
                            
                        elif button_tag == 'menu_btn_close':
                            await call.message.edit_reply_markup()
                    
                        elif button_tag == 'menu_btn_back_menu' or button_tag == 'menu_btn_menu':
                            await call.message.edit_reply_markup()
                            await call.message.edit_text("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard_by_user_data(user_data.user_db_data))
                            
            else:
                await call.message.answer(f"Напиши сначала /start")  
        except Exception as e:
            await error_message(call.message, e, 1)
        
        finally:
            await call.answer()
            
@dp.callback_query(F.data.startswith("admin_btn"))
async def admin_btn_handler(call: types.CallbackQuery):
    if call.message.date > BOT_STARTED_DTTM:
        try:
            user_data: UserDataSchema = await User.validate_bot_access(str(call.from_user.id))
            call_data = call.data.split('__') # <button_tag>__<user_tg_code>
            button_tag = call_data[0]
            choosen_user_tg_code = None
            choosen_request_access_name = None
            
            if len(call_data) > 3:
                choosen_user_tg_code = call_data[2]
                choosen_request_access_name = call_data[3]
    
        
            if user_data.user_db_data:
                if user_data.user_bot_access_data:
                    if user_data.user_bot_access_data.access:
                        if user_data.user_db_data.admin_flg:
                            if button_tag == 'admin_btn_req_bot':
                                requests_data = await Admin().get_bot_requests()
                                rows_qty = 3
                                data = requests_data[:rows_qty]
                                                        
                                schema = ['user_tg_code', 'user_tag', 'access_name', 'processed_dttm']
                                await call.message.edit_text(f"Запросы BOT:\n{get_requests_message(requests_data, schema)}", 
                                                            reply_markup=get_admin_choose_keyboard(user_data.user_db_data, data).as_markup())
                                
                            elif button_tag == 'admin_btn_req_vpn':
                                requests_data = await Admin().get_vpn_requests()
                                rows_qty = 3
                                data = requests_data[:rows_qty]

                                schema = ['user_tg_code', 'user_tag', 'access_name', 'processed_dttm']
                                await call.message.edit_text(f"Запросы VPN:\n{get_requests_message(requests_data, schema)}", 
                                                            reply_markup=get_admin_choose_keyboard(user_data.user_db_data, data).as_markup())
                            
                            elif (button_tag == 'admin_btn_back_menu') or (button_tag == 'admin_btn_secret_menu'):
                                await call.message.edit_text(f"Вот, что я могу для тебя сделать:\n", reply_markup=get_admin_menu_keyboard(user_data.user_db_data))
                            
                            elif button_tag == 'admin_btn_ch_a':
                                if choosen_request_access_name == 'VPN':
                                    resp = await Admin().accept_user_vpn_request(choosen_user_tg_code)
                                    if resp:
                                        if resp['affected'] > 0  or resp['updated'] > 0:
                                                await call.message.edit_text(f'Принял запрос от: {choosen_user_tg_code}, {resp}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                                        else:
                                            await call.message.edit_text(f'Ничего не сделал: {choosen_user_tg_code}, {resp}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                                    else:
                                        await call.message.edit_text(f'Ошибка принять запрос от: {choosen_user_tg_code}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                                
                                if choosen_request_access_name == 'BOT':
                                    resp = await Admin().accept_user_bot_request(choosen_user_tg_code)
                                    if resp:
                                        if resp['affected'] > 0  or resp['updated'] > 0:
                                            await call.message.edit_text(f'Принял запрос от: {choosen_user_tg_code}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                                        else:
                                            await call.message.edit_text(f'Ничего не сделал: {choosen_user_tg_code}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                                    else:
                                        await call.message.edit_text(f'Ошибка принять запрос от: {choosen_user_tg_code}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                                        
                            elif button_tag == 'admin_btn_ch_d':
                                await call.message.edit_text(f'Отклонил запрос от: {choosen_user_tg_code}', reply_markup=get_admin_menu_back_btn(user_data.user_db_data))
                     
        except Exception as e:
                await error_message(call.message, e, 1)
        finally:
            await call.answer()
 
# Message handlers  
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        try:
            admins = await Admin().get_admins_tg_code()
            is_message_user_admin = True if str(message.from_user.id) in admins else False
            add_res = await User.add(str(message.from_user.id), 
                     message.from_user.full_name, 
                     message.from_user.username, 
                     is_message_user_admin
            )
            if add_res:
                if is_message_user_admin:
                    access_resp = await Admin.add_access(str(message.from_user.id))
                    if access_resp:
                        await message.answer(f"Приятно познакомиться, дорогой Админ, {html.bold(message.from_user.full_name)}. Посмотри что можно сделать в /menu")
                    else:
                        await message.answer(f"Ошибка добавления доступа")
                else:
                    await message.answer(f"Приятно познакомиться, {html.bold(message.from_user.full_name)}! Посмотри что можно сделать в /menu")
            else:
                await message.answer(f"Добро пожаловать, {html.bold(message.from_user.full_name)}, посмотри что можно сделать: /menu")
            await message.answer(f"А если хочешь получить больше информации о взаимодествии, то пиши /help или выбирай нужную команду :)")    
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['help']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        try:
            user_data: UserDataSchema = await User.validate_bot_access(str(message.from_user.id))
            if user_data.user_db_data:
                if user_data.user_bot_access_data:
                    if user_data.user_bot_access_data.access:
                        await message.answer(f"Вот, что я могу для тебя сделать:", reply_markup=get_menu_keyboard_by_user_data(user_data.user_db_data))
                    else:
                        await message.answer(f"Тебе стоит обновить подписку /join")
                else:
                    req_resp = await User(user_data.user_db_data).get_bot_request_access()
                    if req_resp:
                        await message.answer("Пожалуйста, дождись одобрения доступа или свяжись с администратором")
                    else:
                        
                        await message.answer("Похоже ты еще не запрашивал доступ. Напиши /join")
            else:
                await message.answer(f"Напиши сначала /start")    
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['admin']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        try:
            user_data: UserDataSchema = await User.validate_bot_access(str(message.from_user.id))
            if user_data.user_db_data:
                if user_data.user_bot_access_data:
                    if user_data.user_bot_access_data.access:
                        if user_data.user_db_data.admin_flg:
                            await message.answer(f"Вот, что я могу для тебя сделать:", reply_markup=get_admin_menu_keyboard(user_data.user_db_data))
                    else:
                        await message.answer(f"Тебе стоит обновить подписку /join")
                else:
                    await message.answer(f"Тебе стоит запросить доступ к боту /join")
            else:
                await message.answer(f"Напиши сначала /start")    
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['join']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        try:
            user_data: UserDataSchema = await User.validate_bot_access(str(message.from_user.id))
            if user_data.user_db_data:
                if user_data.user_bot_access_data:
                    # detect old user
                    if user_data.user_bot_access_data.access:
                        await message.answer(f"Тебе ничего не надо запрашивать, у тебя есть подписка до {user_data.user_bot_access_data.dates[1]}")
                    else:
                        await message.answer(f"У тебя истекла подписка {user_data.user_bot_access_data.dates[1]}")
                        req_resp = await User(user_data.user_db_data).add_bot_access_request()
                        if req_resp:
                            await send_request_message_to_admins(user_data.user_db_data, 'BOT')
                            await message.answer(f"Запросил доступ для тебя. Пожалуйста, дождись его одобрения или свяжись с администратором")
                        elif req_resp == False:
                            await message.answer("Пожалуйста, дождись одобрения доступа или свяжись с администратором")
                        else:
                            await message.answer(f"Ошибка запроса")  
                else:
                    # detect new user                           
                    req_resp = await User(user_data.user_db_data).add_bot_access_request()
                    if req_resp:
                        await send_request_message_to_admins(user_data.user_db_data, 'BOT')
                        await message.answer(f"Запросил доступ для тебя. Пожалуйста, дождись его одобрения или свяжись с администратором")
                    elif req_resp == False:
                        await message.answer(f"У тебя уже есть запрос на доступ!")
                    else:
                        await message.answer(f"Ошибка запроса")
            else:
                await message.answer(f"Напиши сначала /start")    
        except Exception as e:
            await error_message(message, e, 1)
             
@dp.message(Command(commands=['menu']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        try:
            user_data: UserDataSchema = await User.validate_bot_access(str(message.from_user.id))
            if user_data.user_db_data:
                if user_data.user_bot_access_data:
                    if user_data.user_bot_access_data.access and user_data.user_db_data.admin_flg:
                        await message.answer("Aдмин, вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇", reply_markup=get_menu_keyboard_by_user_data(user_data.user_db_data))
                    elif user_data.user_bot_access_data.access and user_data.user_db_data.admin_flg == False:
                        await message.answer("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇", reply_markup=get_menu_keyboard_by_user_data(user_data.user_db_data))
                    elif user_data.user_bot_access_data.access == False:
                        await message.answer(f"Вижу у тебя закончился доступ: {user_data.user_bot_access_data.dates[1]}", reply_markup=get_menu_keyboard_by_user_data(user_data.user_db_data))
                else:
                    req_resp = await User(user_data.user_db_data).get_bot_request_access()
                    if req_resp:
                        await message.answer("Пожалуйста, дождись одобрения доступа или свяжись с администратором")
                    else:
                        await message.answer("Похоже ты еще не запрашивал доступ. Напиши /join")
            else:
                await message.answer(f"Напиши сначала /start")
            
        except Exception as e:
            await error_message(message, e, 1)
     
async def main() -> None:
    if DbManager().check_db_available():
        dbm.create_db()
        logger.info('------------------BOT_STARTED------------------\n')
        await dp.start_polling(bot)
    else:
        raise Exception(f'NO DATABASE CONNECTION!!!')   
                       
if __name__ == "__main__":
    logger = logging.getLogger()
    print(f'------------------DEBUG_MODE: {settings.DEBUG_MODE} ------------------')
    logger.setLevel(logging.DEBUG) if settings.DEBUG_MODE else logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s]-[%(name)s]-%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    #file_handler
    file_handler = logging.FileHandler('./logs/main.log')
    file_handler.setFormatter(formatter)
    
    #console_handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    #handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    #!!!main instance!!!
    try:
        asyncio.run(main())
        logger.info('------------------BOT_DOWN------------------\n')
        
    except Exception as e:
        logger.info('------------------BOT_DOWN------------------\n')
        logging.error(f"Bot crashed with error: {e}. Restarting in 60 seconds...")
    
    
