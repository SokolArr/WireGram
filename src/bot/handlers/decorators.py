from aiogram import types
from functools import wraps
from datetime import datetime, timezone
from logger import MainLogger

logger = MainLogger(__name__).get()

BOT_STARTED_DTTM = datetime.now(tz=timezone.utc)


def new_message(handler):
    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        logger.debug(
            f"get message at: {message.date}, bot started at: "
            f"{BOT_STARTED_DTTM}"
        )
        if message.date >= BOT_STARTED_DTTM:
            return await handler(message, *args, **kwargs)
        else:
            logger.debug(
                f"IGNORE OLD MESSAGE FROM USER {message.from_user.id}"
            )

    return wrapper


def new_сall(handler):
    @wraps(handler)
    async def wrapper(call: types.CallbackQuery, *args, **kwargs):
        logger.debug(
            f"get message at: {call.message.date}, bot started at: "
            f"{BOT_STARTED_DTTM}"
        )
        if call.message.date >= BOT_STARTED_DTTM:
            return await handler(call, *args, **kwargs)
        else:
            logger.debug(
                "IGNORE OLD BUTTON REACTION FROM USER "
                f"{call.message.from_user.id}"
            )

    return wrapper
