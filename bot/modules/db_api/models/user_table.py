from sqlalchemy import Column, Integer, Text, Boolean
from base_table import BaseTable

class UserTable(BaseTable):
    DEFAULT_SCHEMA_NAME = 'main'
    __tablename__       = 'user'
    __table_args__      = {'schema': DEFAULT_SCHEMA_NAME}
    
    user_id =       Column(Integer, primary_key=True, autoincrement=True)
    user_name =     Column(Text, default='NO_USER_NAME')
    user_tg_code =  Column(Text, primary_key=True)
    admin_flg =     Column(Boolean, default=False)