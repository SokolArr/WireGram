import asyncio
from modules.db import DbManager
from bot.main import main as bot_main
from settings import settings
from logger import logger


async def main() -> None:
    logger.info(
        f"-----RUN WITH DEBUG MODE: {str(settings.DEBUG_MODE).upper()}--------"
    )

    if DbManager().check_db_available():
        DbManager().create_db(reinit=False)
        await bot_main()


asyncio.run(main())
