import logging
from datetime import datetime, timezone, timedelta

from .utils.db_manager import DbManager

logger = logging.getLogger(name=__name__+'.py')

class User:
    def __init__(self, db_manager: DbManager = DbManager()):
        self.dbm: DbManager = db_manager
        
    async def check_bot_access(self, user_tg_code: str) -> dict:
        columns = ['user_tg_code',
                   'bot_access_from_dttm',
                   'bot_access_to_dttm']
        
        active_access = await self.dbm.fetch_data(columns=columns, 
                                             schema='main', 
                                             table='v_user_x_user_access', 
                                             condition=f"user_tg_code='{str(user_tg_code)}' and bot_access_from_dttm <= current_timestamp and bot_access_to_dttm > current_timestamp",
                                             limit=1)
        
        expire_active_access = await self.dbm.fetch_data(columns=columns, 
                                             schema='main', 
                                             table='v_user_x_user_access', 
                                             condition=f"user_tg_code='{str(user_tg_code)}'",
                                             limit=1)
                
        if active_access:
            logger.debug(f'user {user_tg_code} have valid BOT access!')
            d = {
                'access': True,
                'dates': (str(active_access[0]['bot_access_from_dttm']), str(active_access[0]['bot_access_to_dttm']))
            }
            return d
        elif expire_active_access:
            logger.debug(f'user {user_tg_code} have NO valid BOT access!')
            d = {
                'access': False,
                'dates': (str(expire_active_access[0]['bot_access_from_dttm']), str(expire_active_access[0]['bot_access_to_dttm']))
            }
            return d
        else:
            d = {
                'access': False,
                'dates': None
            }
            return d
        
    async def check_vpn_access(self, user_tg_code: str):
        columns = ['user_tg_code',
                   'vpn_access_from_dttm',
                   'vpn_access_to_dttm']
        
        active_access = await self.dbm.fetch_data(columns=columns, 
                                             schema='main', 
                                             table='v_user_x_user_access', 
                                             condition=f"user_tg_code='{str(user_tg_code)}' and vpn_access_from_dttm <= current_timestamp and vpn_access_to_dttm > current_timestamp",
                                             limit=1)
        
        expire_active_access = await self.dbm.fetch_data(columns=columns, 
                                             schema='main', 
                                             table='v_user_x_user_access', 
                                             condition=f"user_tg_code='{str(user_tg_code)}'",
                                             limit=1)
                
        if active_access:
            logger.debug(f'user {user_tg_code} have valid BOT access!')
            d = {
                'access': True,
                'dates': (str(active_access[0]['vpn_access_from_dttm']), str(active_access[0]['vpn_access_to_dttm']))
            }
            return d
        elif expire_active_access:
            logger.debug(f'user {user_tg_code} have NO valid BOT access!')
            d = {
                'access': False,
                'dates': (str(expire_active_access[0]['vpn_access_from_dttm']), str(expire_active_access[0]['vpn_access_to_dttm']))
            }
            return d
        else:
            d = {
                'access': False,
                'dates': None
            }
            return d
        
    async def create_access_request(self, user_tg_code:str, user_name:str = 'null'):
        '''
            True if new request was added\n
            False if request already send
        '''
        check_columns = ['sys_inserted_dttm']
        
        ins_columns = ['user_tg_code', 'user_name']
        ins_vals = [(str(user_tg_code), user_name)]

        tz = timezone(timedelta(hours=3)) #TODO tune on prod
        
        check_response = await self.dbm.fetch_data(columns=check_columns, 
                                             schema='main', 
                                             table='user_req_access', 
                                             condition=f"user_tg_code = '{str(user_tg_code)}'")
        
        if check_response:
            inserted_dttm: datetime = check_response[0]['sys_inserted_dttm']
            inserted_dttm = inserted_dttm.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f'user {user_tg_code} already send request to access at {inserted_dttm}!')
            return (False, inserted_dttm)
        
        else:
            logger.info(f'user {user_tg_code} want to consolidate with you!')
            
            await self.dbm.ins_data(columns=ins_columns, 
                                    schema='main', 
                                    table='user_req_access',
                                    vals=ins_vals)
            return (True, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))