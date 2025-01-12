from modules.db_api.models import UserStruct, UserAccessStruct, UserReqAccessStruct
from modules.db_api import DbManager
from datetime import datetime, timedelta

from settings import settings

class Admin():
    dbm = DbManager()
    MAIN_ADMIN_TG_CODE = settings.TG_ADMIN_ID
    MONTH_TIME_DELTA = dbm.MONTH_TIME_DELTA
    
    async def get_admins_tg_code(self) -> list:
        admins = await self.dbm.get_admins()
        tg_codes=[self.MAIN_ADMIN_TG_CODE,]
        for admin in admins:
            tg_codes.append(admin.user_tg_code)      
        return list(set(tg_codes))
    
    async def upgrade_user(self):
        pass
    
    async def downrade_user(self):
        pass
    
    async def get_vpn_requests(self):
        requests = await self.dbm.get_requests_by_request_name('VPN')
        return requests
    
    async def get_bot_requests(self):
        requests = await self.dbm.get_requests_by_request_name('BOT')
        return requests
    
    # async def accept_user_bot_request(self, user_tg_code: str):
    #     access_name = 'BOT'
    #     user: UserStruct = await self.dbm.get_user_by_tg_code(user_tg_code)
    #     if user:
    #         access = UserAccessStruct(
    #                 user_id = user.user_id,
    #                 access_name = access_name,
    #                 access_from_dttm = datetime.now(),
    #                 access_to_dttm = datetime.now() + self.MONTH_TIME_DELTA  
    #         )
    #         if await self.dbm.get_access_by_user_id_access_name(user.user_id, access_name) == None:
    #             res = await self.dbm.delete_access_request_by_user_id_request_name(user.user_id, access_name)
    #             await self.dbm.add_access(access)
    #             return user_tg_code
    #         else:
    #             res = await self.dbm.delete_access_request_by_user_id_request_name(user.user_id, access_name)
    #             await self.dbm.update_request_by_user_id_request_name(user.user_id, access_name, access)
    #             return user_tg_code
        
    # async def accept_user_vpn_request(self, user_tg_code: str):
    #     access_name = 'VPN'
    #     user: UserStruct = await self.dbm.get_user_by_tg_code(user_tg_code)
    #     if user:
    #         access = UserAccessStruct(
    #                 user_id = user.user_id,
    #                 access_name = access_name,
    #                 access_from_dttm = datetime.now(),
    #                 access_to_dttm = datetime.now() + self.MONTH_TIME_DELTA  
    #         )
    #         if await self.dbm.get_access_by_user_id_access_name(user.user_id, access_name) == None:
    #             res = await self.dbm.delete_access_request_by_user_id_request_name(user.user_id, access_name)
    #             await self.dbm.add_access(access)
    #             return user_tg_code
    #         else:
    #             res = await self.dbm.delete_access_request_by_user_id_request_name(user.user_id, access_name)
    #             await self.dbm.update_request_by_user_id_request_name(user.user_id, access_name, access)
    #             return user_tg_code
    
    async def accept_user_bot_request(self, user_tg_code: str):
        access_name = 'BOT'
        resp = await self.dbm.accept_request_by_user_tg_code_request_name(user_tg_code, access_name)
        if resp:
            return {
                'affected': resp[0],
                'updated': resp[1]
            }
        
    async def accept_user_vpn_request(self, user_tg_code: str):
        access_name = 'VPN'
        resp = await self.dbm.accept_request_by_user_tg_code_request_name(user_tg_code, access_name)
        if resp:
            return {
                'affected': resp[0],
                'updated': resp[1]
            }