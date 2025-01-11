import asyncio
import logging
import sys
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from aiogram import F

from models.user import User
from models.admin import Admin
from modules.db_api.manager import DbManager
from modules.db_api.models import UserStruct
from settings import settings

BOT_STARTED_DTTM = datetime.now(tz=timezone.utc)
DTTM_FORMAT = '%Y-%m-%d %H:%M:%S'
DT_FORMAT = '%Y-%m-%d'

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dbm = DbManager()
dp = Dispatcher()



async def main() -> None:
    # await dbm.create_db()
    # await User(UserStruct).test()
    
    if DbManager().check_db_available():
        logger.info('------------------BOT_STARTED------------------\n')
        await dp.start_polling(bot)
    else:
        raise Exception(f'NO database CONNECTION!!!')

async def error_message(message: Message, exeption:str, err_code:int):
    if err_code == 1:
        err_mess = html.pre(f"Возникла критическая ошибка: {datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"+"ERR"+str(err_code))
        logging.error(f'tg_error_message:{err_mess};exeption:{exeption}')
        await message.answer(f"⚠️ Возникла критическая ошибка!\n\n- Отправь письмо с текстом "+html.bold('из следующего cообщения')
                             + " - на почту yamcbot@gmail.com.\n" +
                             "- Если проблема не исправлена, то напиши, пожалуйста, в группу: https://t.me/c/2218172872/16")
        await message.answer(err_mess)   
        
async def sent_request_message_to_admins(user_data, admins: list):
    for admin in admins:
        await bot.send_message(int(admin), f'{html.bold("ВНИМАНИЕ! ЛИЧНОЕ УВЕДОМЛЕНИЕ АДМИНИСТРАТОРА!\n\n")}Пользователь {user_data.user_tg_code}, @{user_data.user_tag} запросил доступ к боту')
    
def get_menu_keyboard(callback_data):
    user_tg_code = callback_data['user_tg_code']
    is_user_admin = callback_data['is_user_admin']
    
    ikb = [
            [InlineKeyboardButton(text="📊 Проверить остатки и баланс", 
                                callback_data=('menu_btn_get_all_status__' + str(user_tg_code))
                                )],
            [InlineKeyboardButton(text="📄 Конфиг для подключения", 
                                callback_data=('menu_btn_get_conf__' + str(user_tg_code))
                                )],
            [InlineKeyboardButton(text="✅ Продлить доступ", 
                                callback_data=('menu_btn_renew_vpn_access__' + str(user_tg_code))
                                )]
        ]
    if is_user_admin:
        ikb.append(
            [InlineKeyboardButton(text="⚠️ АДМИН-МЕНЮ", 
            callback_data=('admin_btn_secret_menu__' + str(user_tg_code))
        )])
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_admin_menu_keyboard(user_tg_code):
    ikb = [
        [InlineKeyboardButton(text="Запросы BOT", 
                              callback_data=('admin_btn_req_bot__' + str(user_tg_code))
                             )],
        [InlineKeyboardButton(text="Запросы VPN", 
                              callback_data=('admin_btn_req_vpn__' + str(user_tg_code))
                             )],
        [InlineKeyboardButton(text="🔤 Открыть пользовательское меню", 
                                callback_data=('menu_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_admin_menu_back_btn(user_tg_code):
    ikb = [
        [InlineKeyboardButton(text="⬅️ Вернуться в админ-меню", 
                                callback_data=('admin_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_back_renew_keyboard(user_tg_code):
    ikb = [
        [InlineKeyboardButton(text="✅ Продлить доступ", 
                              callback_data=('menu_btn_renew_vpn_access__' + str(user_tg_code))
                             )],
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", 
                                callback_data=('menu_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_back_btn(user_tg_code):
    ikb = [
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", 
                                callback_data=('menu_btn_back_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_btn(user_tg_code):
    ikb = [
        [InlineKeyboardButton(text="🔤 Открыть меню", 
                                callback_data=('menu_btn_menu__'+str(user_tg_code))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)
  
def get_requests_message(data, schema: list, max_length: int=1024):
    mess = ''
    for row_id in range(len(data)):
        mess += f'{html.bold(str(row_id + 1))}. '
        for col_id in range(len(data[row_id])):
            mess += (f'{schema[col_id]}: '+ 
                     f'{"@" if schema[col_id]=="user_tag" and data[row_id][col_id] else ""}{data[row_id][col_id]}' 
                     + ', ')
        mess += '\n\n'
    return mess[:max_length]
    
async def get_menu_callback_data(user_data):
    admins = await Admin().get_admins_tg_code()
    is_user_in_admins = user_data.user_tg_code in admins
    is_user_admin = None
    if is_user_in_admins:
        is_user_admin = True
    return {
        'user_tg_code': user_data.user_tg_code,
        'is_user_admin': is_user_admin
    } #TODO maybe not dict, only user_data UserStruct()
    
@dp.callback_query(F.data.startswith("menu_btn"))
async def menu_btn_handler(call: types.CallbackQuery):
    if call.message.date > BOT_STARTED_DTTM:
        call_data = call.data.split('__')
        call_tag = call_data[0]
        user_id = call_data[1]
    
        user_data = UserStruct(
            user_tg_code = user_id
        )
        logging.info(f'USER {user_data.user_tg_code} USED MENU FOR {call_data}')
        try:
            response = await User(user_data).check_bot_acess()
            if response:
                access = response['access']
                if access:
                    callback_data = await get_menu_callback_data(user_data)
                    if call_tag == 'menu_btn_get_conf':
                        await call.message.edit_text(f"{call_tag}",reply_markup=get_menu_back_btn(user_id))
                        vpn_access_data = await User(user_data).check_vpn_acess()
                        if vpn_access_data:
                            if vpn_access_data['access']:
                                await call.message.edit_text("🔎 Ушел искать...")
                                vless_conf = await User(user_data).get_or_create_conn_config()
                                await call.message.edit_text("Вот твой конфиг для подключения.\nCкопируй его нажатием на этот блок:\n"+html.pre(vless_conf))
                                await call.message.answer("Вставь в приложение из буфера обмена.\nПриятного пользования 😃", reply_markup=get_menu_back_btn(user_id))
                            else:
                                await call.message.edit_text("⚠️ У тебя нет активной подписки", reply_markup=get_menu_back_renew_keyboard(user_id))
                        else:
                            await call.message.edit_text("⚠️ У тебя нет активной подписки", reply_markup=get_menu_back_renew_keyboard(user_id))
                        pass

                    elif call_tag == 'menu_btn_get_all_status':
                        # accesses
                        bot_access_data = response
                        vpn_access_data = await User(user_data).check_vpn_acess()
                        vpn_access_mess = f"{html.bold('VPN: (')}"
                        bot_access_mess = f"{html.bold('БОТ: (✅):')}"
                        bot_access_mess += f" доступен с {html.bold(bot_access_data['dates'][0].strftime(DT_FORMAT))} по {html.bold(bot_access_data['dates'][1].strftime(DT_FORMAT))}\n"
                        if vpn_access_data:
                            vpn_access_mess += f"{'✅):' if vpn_access_data['access'] else '⛔️): был'} VPN"
                            vpn_access_mess += f" доступен с {html.bold(vpn_access_data['dates'][0].strftime(DT_FORMAT))} по {html.bold(vpn_access_data['dates'][1].strftime(DT_FORMAT))}\n"
                        else:
                            vpn_access_mess += f"⛔️): нет доступа"
                            
                        # requests
                        vpn_request = html.bold(f'VPN: ')
                        order_status = html.bold(f'Оплата: ')
                        
                        order_data = None #TODO order_data
                        vpn_request_data = await User(user_data).get_vpn_request_access()
                        if vpn_request_data:
                            vpn_request += f'Есть запрос на подписку VPN от {html.bold(vpn_request_data.sys_processed_dttm.strftime(DT_FORMAT))}'
                        else:
                            vpn_request += f'Нет активного запроса на подписку VPN'
                            
                        if order_data:
                            order_status += order_data.order_status #TODO order_status
                        else:
                            order_status += 'Нет данных по заказу'
                            
                        mess = (html.bold('Подписки:\n')+ 
                                bot_access_mess + 
                                vpn_access_mess +
                                html.bold('\n\nЗапросы:\n') +
                                vpn_request + '\n' +
                                order_status)
                        
                        await call.message.edit_text(f"{mess}",reply_markup=get_menu_back_btn(user_id))
                        pass
              
                    elif call_tag == 'menu_btn_renew_vpn_access':
                        await call.message.edit_text(f"{call_tag}",reply_markup=get_menu_back_btn(user_id))
                        resp = await User(user_data).make_new_vpn_request_access()
                        if resp:
                            await call.message.edit_text(f"Запрос направил!",reply_markup=get_menu_back_btn(user_id))
                        else:
                            await call.message.edit_text(f"Запрос или есть или не требуется!",reply_markup=get_menu_back_btn(user_id))
                        pass      
                    
                    elif call_tag == 'menu_btn_close':
                        await call.message.edit_reply_markup()
                    
                    elif call_tag == 'menu_btn_back_menu':
                        await call.message.edit_reply_markup()
                        await call.message.edit_text("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard(callback_data))
                        
                    elif call_tag == 'menu_btn_menu':
                        await call.message.edit_reply_markup()
                        await call.message.answer("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard(callback_data))
            
        except Exception as e:
                await error_message(call.message, e, 1)
        finally:
            await call.answer()
            
@dp.callback_query(F.data.startswith("admin_btn"))
async def admin_btn_handler(call: types.CallbackQuery):
    if call.message.date > BOT_STARTED_DTTM:
        call_data = call.data.split('__')
        call_tag = call_data[0]
        user_id = call_data[1]
    
        user_data = UserStruct(
            user_tg_code = user_id
        )
        logging.info(f'ADMIN {user_data.user_tg_code} USED MENU FOR {call_data}')
        
        try:
            response = await User(user_data).check_bot_acess()
            if response:
                access = response['access']
                admins = await Admin().get_admins_tg_code()
                if access and (user_data.user_tg_code in admins):
                    if call_tag == 'admin_btn_req_bot':
                        vpn_requests_data = await Admin().get_bot_requests()
                                                
                        schema = ['user_tg_code', 'user_tag', 'access_name', 'processed_dttm']
                        await call.message.edit_text(f"Запросы BOT:\n{get_requests_message(vpn_requests_data, schema)}", reply_markup=get_admin_menu_back_btn(user_data.user_tg_code))
                        
                    elif call_tag == 'admin_btn_req_vpn':
                        vpn_requests_data = await Admin().get_vpn_requests()
                        
                        schema = ['user_tg_code', 'user_tag', 'access_name', 'processed_dttm']
                        await call.message.edit_text(f"Запросы VPN:\n{get_requests_message(vpn_requests_data, schema)}", reply_markup=get_admin_menu_back_btn(user_data.user_tg_code))
                    
                    elif (call_tag == 'admin_btn_back_menu') or (call_tag == 'admin_btn_secret_menu'):
                        await call.message.edit_text(f"Вот, что я могу для тебя сделать:\n", reply_markup=get_admin_menu_keyboard(user_data.user_tg_code))
                     
        except Exception as e:
                await error_message(call.message, e, 1)
        finally:
            await call.answer()
    
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        user_data = UserStruct(
            user_tg_code = str(message.from_user.id),
            user_name = message.from_user.full_name,
            user_tag = message.from_user.username
        )
        logging.info(f'USER {user_data.user_tg_code} JUST STARTED DIALOG WITH COMAND /start!')
        try:
            callback_data = await get_menu_callback_data(user_data)
            kb = None
            if await User(user_data).add_new_user():
                await message.answer(f"Привет, я вижу тебя впервые! Приятно познакомиться, {html.bold(user_data.user_name)}!")
                await message.answer(f"Если хочешь получить больше информации о взаимодествии, то пиши /help или выбирай в меню эту команду :)")
            else:
                resp = await User(user_data).check_bot_acess()
                if resp:
                    if resp['access'] == True:
                        kb = get_menu_keyboard(callback_data)
            await message.answer(f"Доброго времени суток, дорогой{' админ' if callback_data['is_user_admin'] else ''}, {html.bold(user_data.user_name)}!", reply_markup=kb)
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['help']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        user_data = UserStruct(
            user_tg_code = str(message.from_user.id),
            user_name = message.from_user.full_name,
            user_tag = message.from_user.username
        )
        logging.info(f'USER {user_data.user_tg_code} USED COMAND /help')
        try:
            response = await User(user_data).check_bot_acess()
            if response:
                access = response['access']
                dttm_to = response['dates'][1]
                if access:
                    callback_data = await get_menu_callback_data(user_data)
                    await message.answer(f"Вот, что я могу для тебя сделать!", reply_markup=get_menu_keyboard(callback_data))
                else:
                    await message.answer(f"⚠️ {html.bold(user_data.user_name)}, твой доступ к этому боту закончился: {dttm_to}.\nНапиши /join чтобы направить запрос на получение доступа")
            else:
                await message.answer(f"⚠️ У тебя нет доступа, {html.bold(user_data.user_name)}!\nНапиши /join чтобы направить запрос на получение доступа")
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['admin']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        user_data = UserStruct(
            user_tg_code = str(message.from_user.id),
            user_name = message.from_user.full_name,
            user_tag = message.from_user.username
        )
        logging.info(f'USER {user_data.user_tg_code} USED COMAND /admin')
        try:
            response = await User(user_data).check_bot_acess()
            if response:
                access = response['access']
                admins = await Admin().get_admins_tg_code()
                if access and (user_data.user_tg_code in admins):
                    await message.answer(f"YOU HAVE {str(user_data.user_tg_code in admins).upper()} ADMIN RIGHTS!")
                    await message.answer(f"Вот, что я могу для тебя сделать:\n", reply_markup=get_admin_menu_keyboard(user_data.user_tg_code))
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['join']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        user_data = UserStruct(
            user_tg_code = str(message.from_user.id),
            user_name = message.from_user.full_name,
            user_tag = message.from_user.username
        )
        logging.info(f'USER {user_data.user_tg_code} USED COMAND /join')
        
        try:
            bot_access_data: dict = await User(user_data).check_bot_acess()
            if bot_access_data:
                # detect old user
                resp = await User(user_data).make_new_bot_request_access() # try to make request
                if resp:    # good try, add new request
                    user_access_data = await User(user_data).check_bot_acess()
                    if user_access_data:
                        await sent_request_message_to_admins(user_data, await Admin().get_admins_tg_code())
                        await message.answer(f"Кажется, что у тебя истекла подписка на бота {user_access_data['dates'][1]}.\nНаправил новый запрос на доступ, не перживай 😉")
                else:       # bad try, no need request
                    user_access_data = await User(user_data).check_bot_acess()
                    if user_access_data:
                        await message.answer(f"Тебе ничего не надо запрашивать, у тебя есть подписка до {user_access_data['dates'][1]}")
                    else:
                        request_acces_data = await User(user_data).get_bot_request_access()
                        await sent_request_message_to_admins(user_data, await Admin().get_admins_tg_code())
                        await message.answer(f"Давай сначала дождемся ответа по запросу от {request_acces_data.sys_processed_dttm.strftime(DTTM_FORMAT)}")
                
            else:
                # detect new user
                await message.answer(f"Привет мой новый друг!")
                if await User(user_data).make_new_bot_request_access():
                    await message.answer(f"Запросил доступ для тебя. Пожалуйста, дождись его одобрения или свяжись с администратором")
                else:
                    request_acces_data = await User(user_data).get_bot_request_access()
                    if request_acces_data:
                        await message.answer(f"Давай сначала дождемся ответа по запросу от {request_acces_data.sys_processed_dttm.strftime(DTTM_FORMAT)}")
                    else:
                        await message.answer(f"Я тебя не знаю 😑!\nНапиши /start, давай познакомимся.")       
        except Exception as e: 
            await error_message(message, e, 1)
    pass
                 
@dp.message(Command(commands=['menu']))
async def command_start_handler(message: Message) -> None:
    if message.date > BOT_STARTED_DTTM:
        user_data = UserStruct(
            user_tg_code = str(message.from_user.id),
            user_name = message.from_user.full_name,
            user_tag = message.from_user.username
        )
        logging.info(f'USER {user_data.user_tg_code} USED COMAND /menu')
        try:
            response = await User(user_data).check_bot_acess()
            if response:
                access = response['access']
                admins = await Admin().get_admins_tg_code()
                is_user_in_admins = user_data.user_tg_code in admins
                callback_data = await get_menu_callback_data(user_data)
                if access and is_user_in_admins:
                    await message.answer("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard(callback_data))
        except Exception as e:
            await error_message(message, e, 1)
                       
if __name__ == "__main__":
    logger = logging.getLogger()
    print(f'------------------DEBUG_MODE: {settings.DEBUG_MODE} ------------------')
    logger.setLevel(logging.DEBUG) if settings.DEBUG_MODE else logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s]-[%(name)s]-%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    #file_handler
    file_handler = logging.FileHandler('./bot/logs/main.log')
    file_handler.setFormatter(formatter)
    
    #console_handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    #handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    #!!!main instance!!!
    asyncio.run(main())
    logger.info('------------------BOT_DOWN------------------\n')  