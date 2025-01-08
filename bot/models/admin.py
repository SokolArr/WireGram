import logging
from datetime import datetime, timezone, timedelta
from py3xui import AsyncApi
from models.user import User

from modules.db_api.db_manager import DbManager
from modules.three_xui_api.vless_api import VlessClientApi, VlessInboundApi

logger = logging.getLogger(name=__name__+'.py')

class Admin(User):
    def __init__(self, vless_api: AsyncApi,db_manager: DbManager = DbManager()):
        self.dbm: DbManager = db_manager
        self.vless_api: AsyncApi = vless_api
        self.tz = timezone(timedelta(hours=0))
        
    async def allow_user_vpn_month_access(self, user_tg_code: str) -> dict:
        response = await self.get_user_data(user_tg_code)
        
        if response:
            user_id = response['user_id']
            now_dttm = datetime.now(tz=self.tz)
            next_month_dttm = now_dttm + timedelta(days=30)
            if response:
                await self.dbm.ins_del_row_data(table_1='user_vpn_access', 
                                                columns_1=["user_id", 'access_from_dttm', 'access_to_dttm'], 
                                                pk_keys_1=["user_id"],
                                                vals_1=(user_id, now_dttm.strftime('%Y-%m-%d %H:%M:%S'), next_month_dttm.strftime('%Y-%m-%d %H:%M:%S')),
                                                table_2='user_vpn_req_access',condition_2='user_tg_code=' + "'" +str(user_tg_code)+"'")
                
    async def allow_user_bot_month_access(self, user_tg_code: str) -> dict:
        response = await self.get_user_data(user_tg_code)
        
        if response:
            user_id = response['user_id']
            now_dttm = datetime.now(tz=self.tz)
            next_month_dttm = now_dttm + timedelta(days=30)
            if response:
                await self.dbm.ins_del_row_data(table_1='user_bot_access', 
                                                columns_1=["user_id", 'access_from_dttm', 'access_to_dttm'], 
                                                pk_keys_1=["user_id"],
                                                vals_1=(user_id, now_dttm.strftime('%Y-%m-%d %H:%M:%S'), next_month_dttm.strftime('%Y-%m-%d %H:%M:%S')),
                                                table_2='user_bot_req_access',condition_2='user_tg_code=' + "'" +str(user_tg_code)+"'")
        
    async def allow_user_pay_access(self, user_tg_code: str) -> dict:
        ''