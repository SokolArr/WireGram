from modules.db_api.models import UserStruct, UserAccessStruct, UserReqAccessStruct
from modules.db_api import DbManager
from modules.db_api.manager import ReturnCodes
from datetime import datetime, timedelta, timezone
from modules.three_xui_api import VlessClientApi

from settings import settings

dbm = DbManager()
MAIN_ADMIN_TG_CODE = settings.TG_ADMIN_ID
MONTH_TIME_DELTA = dbm.MONTH_TIME_DELTA
'''
ReturnCodes(Enum):
    SUCCESS                 = 0
    UNIQUE_VIOLATION        = -1
    FOREIGN_KEY_VIOLATION   = -2
    NOT_FOUND               = -3
    DATABASE_ERROR          = -99
'''

class Admin():
    @staticmethod
    async def get_admins_tg_code() -> list:
        admins = await dbm.get_admins()
        tg_codes=[MAIN_ADMIN_TG_CODE,]
        for admin in admins:
            tg_codes.append(admin.user_tg_code)      
        return list(set(tg_codes))
    
    @staticmethod
    async def upgrade_user():
        pass
    
    @staticmethod
    async def downrade_user():
        pass
    
    @staticmethod  
    async def get_vpn_requests():
        requests = await dbm.get_requests_by_request_name('VPN')
        return requests
    
    @staticmethod
    async def get_bot_requests():
        requests = await dbm.get_requests_by_request_name('BOT')
        return requests
    
    @staticmethod  
    async def accept_user_bot_request(user_tg_code: str):
        access_name = 'BOT'
        resp = await dbm.accept_request_by_user_tg_code_request_name(user_tg_code, access_name)
        if resp:
            return {
                'affected': resp[0],
                'updated': resp[1]
            }
        
    @staticmethod  
    async def accept_user_vpn_request(user_tg_code: str):
        new_time = datetime.now(timezone.utc) + timedelta(600)
        user: UserStruct = await dbm.get_user_by_tg_code(user_tg_code)
        user_id = user.user_id
        access_name = 'VPN'
        try:
            vpn_resp = await VlessClientApi().update_client_expired_time(user_tg_code, new_time)
            db_resp = await dbm.accept_request_by_user_id_request_name(user_id, access_name)
            if db_resp and vpn_resp:
                return {
                    'affected': db_resp[0],
                    'updated': db_resp[1]
                }
        except:
            pass
         
    @staticmethod   
    async def add_access(user_tg_code: str) -> str:
        user: UserStruct = await dbm.get_user_by_tg_code(user_tg_code)
        if user:
            access = UserAccessStruct(
                user_id = user.user_id,
                access_name = 'BOT',
                access_from_dttm = datetime(1970, 1, 1, 0, 0, 0),
                access_to_dttm = datetime(9999, 1, 1, 0, 0, 0)
            )
            resp = await dbm.add_access(access)
            if resp == ReturnCodes.SUCCESS:
                return user_tg_code
            
    @staticmethod   
    async def block_access(user_tg_code: str, access_name: str):
        user: UserStruct = await dbm.get_user_by_tg_code(user_tg_code)
        if user:
            access = UserAccessStruct(
                user_id = user.user_id,
                access_name = access_name,
                access_from_dttm = datetime(1970, 1, 1, 0, 0, 0),
                access_to_dttm = datetime(1970, 1, 1, 0, 0, 0)
            )
            resp = await dbm.update_access(access)
            if resp == ReturnCodes.SUCCESS:
                return user_tg_code
    
    @staticmethod          
    async def update_vless_time(user_tg_code: str, new_time = datetime.now(timezone.utc) + timedelta(600)):
        await VlessClientApi().update_client_expired_time(user_tg_code, new_time)