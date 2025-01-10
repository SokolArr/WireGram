from db_instance import Base, sync_engine, async_engine, session_factory, async_session_factory
from models import UserOrm

import uuid

def create_tables():
    sync_engine.echo = False
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    sync_engine.echo = True

def insert_data():
    user = UserOrm(user_id = uuid.uuid5(uuid.NAMESPACE_DNS, '1234567'),
                user_tg_code = '1234567', 
                user_name = 'Alex', 
                admin_flg = True)
    
    with session_factory() as session:
        session.add(user)
        session.commit()
        
        
async def async_insert_data():
    user = UserOrm(user_id = uuid.uuid5(uuid.NAMESPACE_DNS, '1234567'),
                user_tg_code = '1234567', 
                user_name = 'Alex', 
                admin_flg = True)
    
    async with async_session_factory() as session:
        session.add(user)
        await session.commit()
