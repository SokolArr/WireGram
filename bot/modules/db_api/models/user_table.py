from sqlalchemy import Column, Integer, Text, Boolean
from models.base_table import BaseTable
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass

class UserTable(BaseTable, Base):
    DEFAULT_SCHEMA_NAME = 'main'
    __tablename__       = 'user'
    __table_args__      = {'schema': DEFAULT_SCHEMA_NAME}
    
    user_id =       Column(Integer, primary_key=True, autoincrement=True)
    user_name =     Column(Text, default='NO_USER_NAME')
    user_tg_code =  Column(Text, primary_key=True)
    admin_flg =     Column(Boolean, default=False)