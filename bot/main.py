import asyncio
import logging
import sys
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from modules.bd_api.user import User

import yaml

def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

config = read_yaml_file('./bot/bot_creds.yaml')

TOKEN = config.get('bot_token')

dp = Dispatcher()
bot_user = User()

bot_started_dttm = datetime.now(tz=timezone.utc)

async def check_bot_access(user_tg_code: str) -> tuple:
    bot_access_resp = await bot_user.check_bot_access(user_tg_code=str(user_tg_code))
    if bot_access_resp['access'] == True:
        # print('access good')
        return (True, bot_access_resp['dates'][1])
    elif (bot_access_resp['access'] == False) & (bot_access_resp['dates'] != None):
        # print(f'access expired at' + str({bot_access_resp['dates'][1]}) )
        return (False, bot_access_resp['dates'][1])
    else:
        # print('access denied')
        return (False, None)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.date > bot_started_dttm:
        logging.info(f'user {message.from_user.id} just started dialog!')
        
        (acсess, valid_to_date) = await check_bot_access(message.from_user.id)
        if acсess:
            await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!\nУ тебя есть доступ к этому боту до {valid_to_date}")
        elif (acсess == False) & (valid_to_date != None):
            await message.answer(f"{html.bold(message.from_user.full_name)}, твой доступ к этому боту закончился: {valid_to_date}.\nНапиши /join чтобы направить запрос на получение доступа")
        else:
            await message.answer(f"У тебя нет доступа, {html.bold(message.from_user.full_name)}!\nНапиши /join чтобы направить запрос на получение доступа")
        
@dp.message(Command(commands=['join', 'req_access']))
async def command_start_handler(message: Message) -> None:
    if message.date > bot_started_dttm:
        logging.info(f'user {message.from_user.id} wanted to join!')
        
        (acсess, valid_to_date) = await check_bot_access(message.from_user.id)
        if acсess:
            await message.answer(f"Тебе не нужно запрашивать доступ, он действует до {valid_to_date}!")
        else:
            (is_add, prev_req_dttm) = await bot_user.create_access_request(message.from_user.id, message.from_user.username)
            if is_add:
                await message.answer(f"Запросил доступ для тебя. Пожалуйста, дождись его одобрения или свяжись с администратором")
            else:
                await message.answer(f"Запрос уже был отправлен {prev_req_dttm} UTC, пожалуйста, дождись его одобрения")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, 
                        format='{%(asctime)s}-{%(name)s}-%(levelname)s: %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S', 
                        stream=sys.stdout)
    asyncio.run(main())