from modules.db_api import DbManager
from modules.db_api.models import UserStruct, UserOrderStruct, UserReqAccessStruct, UserAccessStruct
import logging, sys, asyncio, uuid
from datetime import datetime, timedelta, timezone

from modules.three_xui_api import VlessClientApi, VlessInboundApi

class User:
    dbm = DbManager()
    
    def __init__(self, user: UserStruct):
      self.user: UserStruct = user
      
    def __repr__(self):
        return self.user.__repr__()
    
    async def add_new_user(self):
        check_user_tg_code = self.user.user_tg_code
        resp_user = await self.dbm.get_user_by_tg_code(check_user_tg_code)
        if resp_user is not None:
            logging.debug(f'USER: {check_user_tg_code} ALREADY EXIST')
        else:
            new_user = UserStruct(
                user_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(check_user_tg_code)),
                user_tg_code = self.user.user_tg_code,
                user_name = self.user.user_name,
                user_tag = self.user.user_tag,
                admin_flg = False
            )
            user_tg_code = await self.dbm.add_user(new_user)
            return user_tg_code
    
    async def get_user(self):
        return await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
    
    async def make_new_bot_request_access(self):
        user: UserStruct = await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:    
            bot_request_access: UserReqAccessStruct = await self.dbm.get_request_by_user_id_request_name(user.user_id, 'BOT')
            if (user.user_id) and (bot_request_access is None):
                user_tg_code = self.user.user_tg_code
                req = UserReqAccessStruct(
                    user_id = user.user_id,
                    req_access_name = 'BOT'
                )
                await self.dbm.add_request(req)
                return user_tg_code
        else: 
            return None
        
    async def get_bot_request_access(self):
        user: UserStruct = await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:    
            request_access: UserReqAccessStruct = await self.dbm.get_request_by_user_id_request_name(user.user_id, 'BOT')
            return request_access
        
    async def get_vpn_request_access(self):
        user: UserStruct = await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:    
            request_access: UserReqAccessStruct = await self.dbm.get_request_by_user_id_request_name(user.user_id, 'VPN')
            return request_access
    
    async def make_new_vpn_request_access(self):
        user: UserStruct = await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            vpn_request_access: UserReqAccessStruct = await self.dbm.get_request_by_user_id_request_name(user.user_id, 'VPN')
            if (user.user_id) and (vpn_request_access is None):
                user_tg_code = self.user.user_tg_code
                req = UserReqAccessStruct(
                    user_id = user.user_id,
                    req_access_name = 'VPN'
                )
                await self.dbm.add_request(req)
                return user_tg_code
        else: 
            return None
    
    async def make_new_order(self):
        pass
    
    async def check_bot_acess(self):
        """return {
            'access': True,
            'dates': [access_from_dttm: <datetime>, access_to_dttm: <datetime>]
        }"""
        user: UserStruct = await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            access: UserAccessStruct = await self.dbm.get_access_by_user_id_access_name(user.user_id, 'BOT')
            if access:
                if (access.access_from_dttm <= datetime.now()) and (access.access_to_dttm > datetime.now()):
                    return {
                        'access': True,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }
                elif (access.access_to_dttm < datetime.now()):
                    return {
                        'access': False,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }
            else: return None #no data in access table!
                                
    async def check_vpn_acess(self):
        """return {
            'access': True,
            'dates': [<datetime>, <datetime>]
        }"""
        user: UserStruct = await self.dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            access: UserAccessStruct = await self.dbm.get_access_by_user_id_access_name(user.user_id, 'VPN')
            if access:
                if (access.access_from_dttm <= datetime.now()) and (access.access_to_dttm > datetime.now()):
                    return {
                        'access': True,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }
                else:
                    return {
                        'access': False,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }

    async def get_or_create_conn_config(self):
        main_inbound_id = await VlessInboundApi().get_inbounds_id_by_remark('main')
        await VlessClientApi().make_vless_client(main_inbound_id, self.user.user_tg_code,)
        return await VlessClientApi().get_vless_client_link_by_email(self.user.user_tg_code)



