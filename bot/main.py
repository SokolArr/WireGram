import asyncio
import logging
import sys
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, html, types, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.bd_api.models.user import User

import yaml

def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

config = read_yaml_file('./bot/bot_creds.yaml')
prefs = read_yaml_file('./bot/prefs.yaml')
TOKEN = config.get('bot_token')

dp = Dispatcher()

bot_user = User()
bot_started_dttm = datetime.now(tz=timezone.utc)

async def error_message(message: Message, exeption:str, err_code:int):
    if err_code == 1:
        err_mess = html.pre(f"Возникла критическая ошибка: {datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"+"ERR"+str(err_code))
        logging.error(f'tg_error_message:{err_mess};exeption:{exeption}')
        await message.answer(f"⚠️ Возникла критическая ошибка!\n\n- Отправь письмо с текстом "+html.bold('из следующего cообщения')
                             + " - на почту yamcbot@gmail.com.\n" +
                             "- Если проблема не исправлена, то напиши, пожалуйста, в группу: https://t.me/c/2218172872/16")
        await message.answer(err_mess)

async def get_bot_access(user_tg_code: str) -> tuple:
    try:
        bot_access_resp = await bot_user.get_bot_access_data(user_tg_code=str(user_tg_code))
        return (bot_access_resp['access'], bot_access_resp['date_to'])
    except Exception as e:
        raise e
    
async def get_vpn_access(user_tg_code: str) -> tuple:
    try:
        bot_access_resp = await bot_user.get_vpn_access_data(user_tg_code=str(user_tg_code))
        return (bot_access_resp['access'], bot_access_resp['date_to'])
    except Exception as e:
        raise e
   
def get_menu_keyboard(user_id):
    ikb = [
        [InlineKeyboardButton(text="📄 Конфиг для подключения", 
                                callback_data=('menu_btn_get_conf__'+str(user_id))
                                )],
        [InlineKeyboardButton(text="📋 Статус по всем привилегиям", 
                                callback_data=('menu_btn_get_all_status__'+str(user_id))
                                )],
        [InlineKeyboardButton(text="✅ Продлить доступ", 
                                callback_data=('menu_btn_renew_vpn_access__'+str(user_id))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_back_btn(user_id):
    ikb = [
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", 
                                callback_data=('menu_btn_back_menu__'+str(user_id))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)

def get_menu_btn(user_id):
    ikb = [
        [InlineKeyboardButton(text="🔤 Открыть меню", 
                                callback_data=('menu_btn_menu__'+str(user_id))
                                )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=ikb)
    
@dp.callback_query(F.data.startswith("menu_btn"))
async def menu_btn_handler(call: types.CallbackQuery):
    if call.message.date > bot_started_dttm:
        call_data = call.data.split('__')
        call_tag = call_data[0]
        user_id = call_data[1]
        try:
            (acсess, valid_to_date) = await get_bot_access(user_id)
            if acсess:
                if call_tag == 'menu_btn_get_conf':
                    await call.message.answer('Мяу вместо конфига')
                elif call_tag == 'menu_btn_get_conf':   
                    pass
                elif call_tag == 'menu_btn_get_all_status':
                    (vpn_access, valid_to_date) = await get_vpn_access(user_id)

                    pay_request = False
                    max_speed = 8
                    
                    vpn_access_mess = html.bold("Доступ к VPN: ") + (f"✅\n- действует до {valid_to_date}" if vpn_access else "⛔️\n - нет") + "\n\n"
                    pay_request_mess = html.bold("Запрос на оплату: ") + ("✅\n - есть [from]" if pay_request else "⛔️\n - не нашел активных запросов") + "\n\n"
                    max_speed_mess = html.bold("Максимальная скорость соединения:\n") + "- "+ str(max_speed) + "Mb/s"
                    
                    status_mess  = vpn_access_mess + pay_request_mess + max_speed_mess
                    
                    await call.message.edit_text(f"{status_mess}", reply_markup=get_menu_back_btn(user_id))
                                
                elif call_tag == 'menu_btn_renew_vpn_access':   
                    await call.message.answer('Не спеши, не готово еще')
                
                elif call_tag == 'menu_btn_close':
                    await call.message.edit_reply_markup()
                
                elif call_tag == 'menu_btn_back_menu':
                    await call.message.edit_reply_markup()
                    await call.message.edit_text("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard(user_id))
                    
                elif call_tag == 'menu_btn_menu':
                    await call.message.edit_reply_markup()
                    await call.message.answer("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard(user_id))
        except Exception as e:
                await error_message(call.message, e, 1)
        finally:
            await call.answer()
    
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.date > bot_started_dttm:
        logging.info(f'user {message.from_user.id} just started dialog!')
        
        try:
            (acсess, valid_to_date) = await get_bot_access(message.from_user.id)
            if acсess:
                await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!", reply_markup=get_menu_btn(message.from_user.id))
            elif (acсess == False) & (valid_to_date != None):
                await message.answer(f"⚠️ {html.bold(message.from_user.full_name)}, твой доступ к этому боту закончился: {valid_to_date}.\nНапиши /join чтобы направить запрос на получение доступа")
            else:
                await message.answer(f"⚠️ У тебя нет доступа, {html.bold(message.from_user.full_name)}!\nНапиши /join чтобы направить запрос на получение доступа")
                
        except Exception as e:
            await error_message(message, e, 1)
            
@dp.message(Command(commands=['join']))
async def command_start_handler(message: Message) -> None:
    if message.date > bot_started_dttm:
        logging.info(f'user {message.from_user.id} wanted to join!')
        try:
            (acсess, valid_to_date) = await get_bot_access(message.from_user.id)
            if acсess:
                await message.answer(f"У тебя уже есть доступ до {valid_to_date}!")
            else:
                (is_add, prev_req_dttm) = await bot_user.create_access_request(message.from_user.id, message.from_user.username)
                if is_add:
                    await message.answer(f"Запросил доступ для тебя. Пожалуйста, дождись его одобрения или свяжись с администратором")
                else:
                    await message.answer(f"Запрос уже был отправлен {prev_req_dttm} UTC, пожалуйста, дождись его одобрения")
                    
        except Exception as e:
            await error_message(message, e, 1)
                 
@dp.message(Command(commands=['menu']))
async def command_start_handler(message: Message) -> None:
    if message.date > bot_started_dttm:
        try:
            (acсess, _) = await get_bot_access(message.from_user.id)
            if acсess:                
                await message.answer("Вот, что я могу сделать для тебя!\nНажми на нужную кнопку ниже 😇",reply_markup=get_menu_keyboard(message.from_user.id))
                    
        except Exception as e:
            await error_message(message, e, 1)
                       
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))    
    await dp.start_polling(bot)

if __name__ == "__main__":
    logger = logging.getLogger()    
    logger.setLevel(logging.DEBUG) if prefs.get('main_prefs')['debug_mode'] else logger.setLevel(logging.INFO)
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