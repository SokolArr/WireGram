from sqlalchemy import Column, Integer, Text, TIMESTAMP
from base_table import BaseTable

class UserAccessTable(BaseTable):
    DEFAULT_SCHEMA_NAME = 'main'
    __tablename__       = 'user_access'
    __table_args__      = {'schema': DEFAULT_SCHEMA_NAME}
    
    user_id =           Column(Integer, primary_key=True)
    access_name =       Column(Text, primary_key=True)
    access_from_dttm =  Column(TIMESTAMP)
    access_to_dttm =    Column(TIMESTAMP)