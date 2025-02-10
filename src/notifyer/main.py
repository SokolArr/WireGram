import psycopg
import os
import asyncio
import zoneinfo
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import Bot

load_dotenv()
q = """
    select 
        u.user_tg_id,
        usc.config_name,
        usc.valid_from_dttm,
        usc.valid_to_dttm
    from
        wg.user_service_config usc
    join
        wg.user u
    on 
        usc.user_id = u.user_id
        and usc.valid_from_dttm <= current_timestamp
        and usc.valid_to_dttm > current_timestamp
    order by
        1, 2
"""

db_conn = {
    "dbname": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "host": os.environ.get("DB_HOST"),
    "port": os.environ.get("DB_PORT"),
}

TZ = zoneinfo.ZoneInfo(os.environ.get("TZ"))

bot = Bot(
    token=os.environ.get("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


async def main():
    users_configs = []
    with psycopg.connect(**db_conn) as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            res = cur.fetchall()
            for row in res:
                users_configs.append(row)

    now_dttm = datetime.now() + timedelta(hours=3)
    for config in users_configs:
        user_tg_id = config[0]
        valid_to_dttm: datetime = config[3]
        if valid_to_dttm - timedelta(1) < now_dttm:
            delta: timedelta = valid_to_dttm - now_dttm
            days_left = delta.days
            left_ph = ""
            if days_left == 0:
                left_ph = f"{int(delta.total_seconds() // 3600)}ч."
            else:
                left_ph = f"{delta.days}дн."
            mess = (
                f"Привет 👋\nТвоя подписка для конфигурации {config[1]} "
                f"закончится через {left_ph} "
                f"({valid_to_dttm.strftime('%Y-%m-%d %H:%M:%S')})"
            )
            print(now_dttm, mess)
            await bot.send_message(user_tg_id, mess)


if __name__ == "__main__":
    asyncio.run(main())
