import logging
from datetime import datetime, timezone, timedelta

from .utils.db_manager import DbManager

logger = logging.getLogger(name=__name__+'.py')

class User:
    def __init__(self, db_manager: DbManager = DbManager()):
        self.dbm: DbManager = db_manager
        
    async def check_valid_access(self, user_tg_code: str) -> bool:
        columns = ['user_id',
                   'user_tg_code',
                   'valid_flg',
                   'access_from_dt',
                   'access_to_dt']
    
        response = await self.dbm.fetch_data(columns=columns, 
                                             schema='main', 
                                             table='v_user_x_user_access', 
                                             condition=f"user_tg_code='{str(user_tg_code)}' and valid_flg = True",
                                             limit=1)
        if response:
            logger.debug(f'user {user_tg_code} have valid user access!')
            return True
        else:
            logger.debug(f'user {user_tg_code} have NO valid user access!')
            return False
        
    async def create_access_request(self, user_tg_code, user_name):
        '''
            True if new request was added\n
            False if request already send
        '''
        check_columns = ['inserted_dttm']
        
        ins_columns = ['user_tg_code', 'user_name']
        ins_vals = [(str(user_tg_code), user_name)]

        tz = timezone(timedelta(hours=3)) #TODO tune on prod
        
        check_response = await self.dbm.fetch_data(columns=check_columns, 
                                             schema='main', 
                                             table='user_req_access', 
                                             condition=f"user_tg_code = '{str(user_tg_code)}'")
        
        if check_response:
            inserted_dttm: datetime = check_response[0]['inserted_dttm']
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