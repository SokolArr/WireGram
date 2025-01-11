from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import DeclarativeBase
from settings import settings

import enum

MAIN_SCHEMA_NAME = settings.DB_main_schema_name
WRITE_LOGS = settings.DB_write_logs

class Fold(enum.Enum):
    pass

class Base(DeclarativeBase):
    repr_cols_num = 10
    repr_cols = tuple()
    
    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()): 
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append (f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__} {', '.join(cols)}>"
    pass

class BaseLog(DeclarativeBase):
    pass

sync_engine = create_engine(
    url=settings.DB_URL_psycopg,
    echo=True,
    # pool_size=5,
    # max_overflow=10,
)

async_engine = create_async_engine(
    url=settings.DB_URL_asyncpg,
    echo=True
)

session_factory = sessionmaker(sync_engine)
async_session_factory = async_sessionmaker(async_engine, expire_on_commit = True)

