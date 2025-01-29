from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from settings import settings

class DBSettings():
    WRITE_LOGS_FLG:bool      = settings.WRITE_LOGS
    
    DEFAULT_TIMEZONE:str     = settings.DEFAULT_TIMEZONE
    DEFAULT_SCHEMA_NAME:str  = settings.DB_DEFAULT_SCHEMA_NAME

    WG_USER: str = settings.DB_WG_USER
    WG_PASS: str = settings.DB_WG_PASS

    # ADMIN DB:
    admin_sync_engine = create_engine(
        url=settings.DB_ADMIN_URL_psycopg,
        # echo=True,
        pool_size=5,
        max_overflow=10
    )
    admin_async_engine = create_async_engine(
        url=settings.DB_ADMIN_URL_asyncpg,
        echo=True
    )
    admin_session_factory = sessionmaker(admin_sync_engine)
    admin_async_session_factory = async_sessionmaker(admin_async_engine, expire_on_commit = True)
    
    #WIREGRAM USER
    sync_engine = create_engine(
        url=settings.DB_WG_USER_URL_psycopg,
        echo=True,
        pool_size=5,
        max_overflow=10
    )
    async_engine = create_async_engine(
        url=settings.DB_WG_USER_URL_asyncpg,
        echo=True
    )
    session_factory = sessionmaker(sync_engine)
    async_session_factory = async_sessionmaker(async_engine, expire_on_commit = True)
    

