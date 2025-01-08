import logging
from datetime import datetime, timezone, timedelta
from py3xui import AsyncApi

from modules.db_api.db_manager import DbManager
from modules.three_xui_api.vless_api import VlessClientApi, VlessInboundApi

logger = logging.getLogger(name=__name__+'.py')

class User:
    def __init__(self, vless_api: AsyncApi,db_manager: DbManager = DbManager()):
        self.dbm: DbManager = db_manager
        self.vless_api: AsyncApi = vless_api
        
    async def get_user_data(self, user_tg_code: str) -> dict:
        columns = ['user_id','user_name','user_tg_code','admin_flg']
        
        response = await self.dbm.fetch_data(columns=columns, 
                                schema='main', 
                                table='user', 
                                condition=f"user_tg_code='{str(user_tg_code)}'",
                                limit=1)
        if response:
            response = response[0]
            return {
                'user_id': response['user_id'],
                'user_name': response['user_name'],
                'user_tg_code': response['user_tg_code'],
                'admin_flg': response['admin_flg']
            }
        else:
            return None
        
    async def get_bot_access_data(self, user_tg_code: str) -> dict:
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
            active_access = active_access[0]
            logger.debug(f'user {user_tg_code} have valid BOT access!')
            return {
                'access': True,
                'tuple_dates': (str(active_access['bot_access_from_dttm']), str(active_access['bot_access_to_dttm'])),
                'date_from': str(active_access['bot_access_from_dttm']),
                'date_to': str(active_access['bot_access_to_dttm'])
            }
        elif expire_active_access:
            expire_active_access = expire_active_access[0]
            logger.debug(f'user {user_tg_code} have NO valid BOT access!')
            return {
                'access': False,
                'tuple_dates': (str(expire_active_access['bot_access_from_dttm']), str(expire_active_access['bot_access_to_dttm'])),
                'date_from': str(expire_active_access['bot_access_from_dttm']),
                'date_to': str(expire_active_access['bot_access_to_dttm'])
            }
        else:
            return {
                'access': False,
                'tuple_dates': None,
                'date_from': None,
                'date_to': None
            }
        
    async def get_vpn_access_data(self, user_tg_code: str):
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
            active_access = active_access[0]
            logger.debug(f'user {user_tg_code} have valid VPN access!')
            return {
                'access': True,
                'tuple_dates': (str(active_access['vpn_access_from_dttm']), str(active_access['vpn_access_to_dttm'])),
                'date_from': str(active_access['vpn_access_from_dttm']),
                'date_to': str(active_access['vpn_access_to_dttm'])
            }
        elif expire_active_access:
            expire_active_access = expire_active_access[0]
            logger.debug(f'user {user_tg_code} have NO valid VPN access!')
            return {
                'access': False,
                'tuple_dates': (str(expire_active_access['vpn_access_from_dttm']), str(expire_active_access['vpn_access_to_dttm'])),
                'date_from': str(expire_active_access['vpn_access_from_dttm']),
                'date_to': str(expire_active_access['vpn_access_to_dttm'])
            }
        else:
            return {
                'access': False,
                'tuple_dates': None,
                'date_from': None,
                'date_to': None
            }
        
    async def get_or_create_bot_access_request(self, user_tg_code:str, user_name:str = 'null'):
        '''
            True if new request was added\n
            False if request already send
        '''
        check_columns = ['sys_inserted_dttm']
        
        ins_columns = ['user_tg_code', 'user_name']
        ins_vals = (str(user_tg_code), user_name)

        tz = timezone(timedelta(hours=3)) #TODO tune on prod
        
        check_response = await self.dbm.fetch_data(columns=check_columns, 
                                             schema='main', 
                                             table='user_bot_req_access', 
                                             condition=f"user_tg_code = '{str(user_tg_code)}'")
        
        if check_response:
            inserted_dttm: datetime = check_response[0]['sys_inserted_dttm']
            inserted_dttm = inserted_dttm.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f'user {user_tg_code} already send request to access at {inserted_dttm}!')
            return (False, inserted_dttm)
        
        else:
            logger.info(f'user {user_tg_code} want to consolidate with you!')
            
            await self.dbm.ins_row_delbefore_data(columns=ins_columns,
                                                pk_keys=['user_tg_code'],
                                                schema='main', 
                                                table='user_bot_req_access',
                                                vals=ins_vals)
            return (True, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    async def get_or_create_vpn_access_request(self, user_tg_code:str, user_name:str = 'null'):
        '''
            True if new request was added\n
            False if request already send
        '''
        check_columns = ['sys_inserted_dttm']
        
        ins_columns = ['user_tg_code', 'user_name']
        ins_vals = (str(user_tg_code), user_name)

        tz = timezone(timedelta(hours=3)) #TODO tune on prod
        
        check_response = await self.dbm.fetch_data(columns=check_columns, 
                                             schema='main', 
                                             table='user_vpn_req_access', 
                                             condition=f"user_tg_code = '{str(user_tg_code)}'")
        
        if check_response:
            inserted_dttm: datetime = check_response[0]['sys_inserted_dttm']
            inserted_dttm = inserted_dttm.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f'user {user_tg_code} already send request to access at {inserted_dttm}!')
            return (False, inserted_dttm)
        
        else:
            logger.info(f'user {user_tg_code} want to consolidate with you!')
            
            await self.dbm.ins_row_delbefore_data(columns=ins_columns,
                                                pk_keys=['user_tg_code'],
                                                schema='main', 
                                                table='user_vpn_req_access',
                                                vals=ins_vals)
            return (True, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    async def get_or_create_pay_request(self, user_tg_code:str, user_name:str = 'null'):
        '''
            True if new request was added\n
            False if request already send
        '''
        check_columns = ['sys_inserted_dttm']
        
        ins_columns = ['user_tg_code', 'user_name']
        ins_vals = (str(user_tg_code), user_name)

        tz = timezone(timedelta(hours=3)) #TODO tune on prod
        
        check_response = await self.dbm.fetch_data(columns=check_columns, 
                                             schema='main', 
                                             table='user_pay_req', 
                                             condition=f"user_tg_code = '{str(user_tg_code)}'")
        
        if check_response:
            inserted_dttm: datetime = check_response[0]['sys_inserted_dttm']
            inserted_dttm = inserted_dttm.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f'user {user_tg_code} already send request to access at {inserted_dttm}!')
            return (False, inserted_dttm)
        
        else:
            logger.info(f'user {user_tg_code} want to consolidate with you!')
            
            await self.dbm.ins_row_delbefore_data(columns=ins_columns,
                                                pk_keys=['user_tg_code'],
                                                schema='main', 
                                                table='user_pay_req',
                                                vals=ins_vals)
            return (True, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    async def get_pay_request_data(self, user_tg_code:str):
        check_columns = ['sys_inserted_dttm']
        tz = timezone(timedelta(hours=3)) #TODO tune on prod
        check_response = await self.dbm.fetch_data(columns=check_columns, 
                                             schema='main', 
                                             table='user_pay_req', 
                                             condition=f"user_tg_code = '{str(user_tg_code)}'")
        if check_response:
            inserted_dttm: datetime = check_response[0]['sys_inserted_dttm']
            inserted_dttm = inserted_dttm.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f'user {user_tg_code} pay request were sand at {inserted_dttm}!')
            return (True, inserted_dttm)
        else:
            return (False, None)
        
    async def get_or_create_conn_config(self, user_tg_code:str):
        cl = VlessClientApi(api=self.vless_api)
        inb = VlessInboundApi(api=self.vless_api)
        main_inbound_id = await inb.get_inbounds_id_by_remark('main')
        await cl.make_vless_client(main_inbound_id, user_tg_code,)
        return await cl.get_vless_client_link_by_email(user_tg_code)