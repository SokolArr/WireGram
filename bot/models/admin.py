from modules.db_api.models import UserStruct, UserAccessStruct, UserReqAccessStruct
from .user import User
from modules.db_api import DbManager
from datetime import datetime,timedelta

from settings import settings

class Admin():
    dbm = DbManager()
    main_admin_tg_code = settings.TG_ADMIN_ID
    
    MONTH_TIME_DELTA = timedelta(30)
    
    async def get_admins_tg_code(self) -> list:
        admins = await self.dbm.get_admins()
        tg_codes=[self.main_admin_tg_code,]
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
    
    async def accept_user_bot_request(self, user_tg_code: str):
        user: UserStruct = await self.dbm.get_user_by_tg_code(user_tg_code)
        if user:
            acess = UserAccessStruct(
                user_id = user.user_id,
                access_name = 'BOT',
                access_from_dttm = datetime.now(),
                access_to_dttm = datetime.now() + self.MONTH_TIME_DELTA  
            )
            self.dbm.add_access(acess)
            #TODO del from request
            return user_tg_code
        
    
    async def accept_user_vpn_request():
        pass
    