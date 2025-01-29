from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot.handlers.decorators import new_message, new_сall
from bot.handlers.commands.admin import admin_cmd
from bot.handlers.commands.help import help_cmd
from bot.handlers.commands.join import join_cmd
from bot.handlers.commands.menu import menu_cmd
from bot.handlers.commands.start import start_cmd

from bot.handlers.callbacks.admin import admin_cb_cmd
from bot.handlers.callbacks.menu import menu_cb_cmd
from bot.handlers.callbacks.config import serv_cb_cmd

router = Router()

@router.message(Command('admin'))
@new_message
async def admin_handler(message: Message):
    await admin_cmd(message)
    
@router.message(Command('help'))
@new_message
async def help_handler(message: Message):
    await help_cmd(message)

@router.message(Command('join'))
@new_message
async def join_handler(message: Message):
    await join_cmd(message)

@router.message(Command('menu'))
@new_message
async def menu_handler(message: Message):
    await menu_cmd(message)
    
@router.message(CommandStart())
@new_message
async def start_handler(message: Message):
    await start_cmd(message)

@router.callback_query(F.data.startswith("admin"))
@new_сall
async def admin_btn_handler(call: CallbackQuery):
    await admin_cb_cmd(call)
    
@router.callback_query(F.data.startswith("menu"))
@new_сall
async def menu_btn_handler(call: CallbackQuery):
    await menu_cb_cmd(call)
    
@router.callback_query(F.data.startswith("serv"))
@new_сall
async def serv_btn_handler(call: CallbackQuery):
    await serv_cb_cmd(call)