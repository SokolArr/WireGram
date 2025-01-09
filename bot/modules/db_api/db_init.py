from sqlalchemy.ext.asyncio import create_async_engine
from models import UserTable, UserAccessTable

async def init_db(db_url = ''):
    engine = create_async_engine(db_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(UserTable.metadata.create_all)
        await conn.run_sync(UserAccessTable.metadata.create_all)