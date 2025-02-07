import asyncio
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from settings import settings
from logger import MainLogger
from bot.handlers import router

BOT_STARTED_DTTM = datetime.now(tz=timezone.utc)
DTTM_FORMAT = "%Y-%m-%d %H:%M:%S"
DT_FORMAT = "%Y-%m-%d"

logger = MainLogger(__name__).get()

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


async def main() -> None:
    try:
        logger.info("v--------START_BOT--------v")
        dp.include_router(router)
        await dp.start_polling(bot)
        logger.info("^--------STOP_BOT--------^")

    except Exception as e:
        logger.info("^--------STOP_BOT--------^")
        await bot.send_message(
            int(settings.TG_ADMIN_ID), f"DOWN WITH ERROR: {e}"
        )
        await asyncio.sleep(5)
