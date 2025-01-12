from modules.db_api import DbManager
from modules.db_api.manager import now_dttm
from modules.db_api.models import UserStruct, UserOrderStruct, UserReqAccessStruct, UserAccessStruct
import logging, sys, asyncio, uuid
from datetime import datetime, timedelta, timezone
from dotmap import DotMap

from pydantic import BaseModel

from .admin import Admin
from modules.three_xui_api import VlessClientApi, VlessInboundApi

dbm = DbManager()

class UserAccessDataSchema(BaseModel):
    access: bool
    dates: list[datetime]
    
class UserDataSchema(BaseModel):
    user: str
    user_db_data: UserStruct
    user_bot_access_data: UserAccessDataSchema
    user_vpn_access_data: UserAccessDataSchema

class User:
    def __init__(self, user: UserStruct = None):
      self.user: UserStruct = user
      
    def __repr__(self):
        return self.user.__repr__()
    
    @staticmethod
    async def add(user_tg_code, user_name, user_tag, admin_flg):
        resp_user = await dbm.get_user_by_tg_code(user_tg_code)
        if resp_user is not None:
            logging.debug(f'USER: {user_tg_code} ALREADY EXIST!')
        else:
            new_user = UserStruct(
                user_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(user_tg_code)),
                user_tg_code = user_tg_code,
                user_name = user_name,
                user_tag = user_tag,
                admin_flg = admin_flg
            )
            user_tg_code = await dbm.add_user(new_user)
            return user_tg_code
    
    async def get(self):
        return await dbm.get_user_by_tg_code(self.user.user_tg_code)
    
    async def add_bot_access_request(self):
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:    
            bot_request_access: UserReqAccessStruct = await dbm.get_request_by_user_id_request_name(user.user_id, 'BOT')
            if bot_request_access is None:
                req = UserReqAccessStruct(
                    user_id = user.user_id,
                    req_access_name = 'BOT'
                )
                await dbm.add_request(req)
                return True
            else:
                return False
                
        
    async def get_bot_request_access(self):
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:    
            request_access: UserReqAccessStruct = await dbm.get_request_by_user_id_request_name(user.user_id, 'BOT')
            return request_access
        
    async def get_vpn_request_access(self):
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:    
            request_access: UserReqAccessStruct = await dbm.get_request_by_user_id_request_name(user.user_id, 'VPN')
            return request_access
    
    async def make_new_vpn_request_access(self):
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            vpn_request_access: UserReqAccessStruct = await dbm.get_request_by_user_id_request_name(user.user_id, 'VPN')
            if (user.user_id) and (vpn_request_access is None):
                user_tg_code = self.user.user_tg_code
                req = UserReqAccessStruct(
                    user_id = user.user_id,
                    req_access_name = 'VPN'
                )
                await dbm.add_request(req)
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
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            access: UserAccessStruct = await dbm.get_access_by_user_id_access_name(user.user_id, 'BOT')
            if access:
                if (access.access_from_dttm <= now_dttm()) and (access.access_to_dttm > now_dttm()):
                    return {
                        'access': True,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }
                elif (access.access_to_dttm < now_dttm()):
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
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            access: UserAccessStruct = await dbm.get_access_by_user_id_access_name(user.user_id, 'VPN')
            if access:
                if (access.access_from_dttm <= now_dttm()) and (access.access_to_dttm > now_dttm()):
                    return {
                        'access': True,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }
                else:
                    return {
                        'access': False,
                        'dates': [access.access_from_dttm, access.access_to_dttm]
                    }

    async def get_or_create_vless_config(self):
        await VlessInboundApi().make_vless_inbound('main', 1032)
        main_inbound_id = await VlessInboundApi().get_inbounds_id_by_remark('main')
        await VlessClientApi().make_vless_client(main_inbound_id, self.user.user_tg_code,)
        return await VlessClientApi().get_vless_client_link_by_email(self.user.user_tg_code)

    @staticmethod
    async def validate_bot_access(user_tg_code: str):
        user: UserStruct = await dbm.get_user_by_tg_code(user_tg_code)
        user_bot_access_data = None
        user_vpn_access_data = None
        if user:
            # BOT access:
            user_bot_access = await dbm.get_access_by_user_id_access_name(user.user_id, 'BOT')
            if user_bot_access:
                
                if (user_bot_access.access_from_dttm <= now_dttm()) and (user_bot_access.access_to_dttm > now_dttm()):
                    user_bot_access_data = {
                        'access': True,
                        'dates': [user_bot_access.access_from_dttm, user_bot_access.access_to_dttm]
                    }
                elif (user_bot_access.access_to_dttm < now_dttm()):
                    user_bot_access_data = {
                        'access': False,
                        'dates': [user_bot_access.access_from_dttm, user_bot_access.access_to_dttm]
                    }
                    
            # VPN access:
            user_vpn_access = await dbm.get_access_by_user_id_access_name(user.user_id, 'VPN')
            if user_vpn_access:
                
                if (user_vpn_access.access_from_dttm <= now_dttm()) and (user_vpn_access.access_to_dttm > now_dttm()):
                    user_vpn_access_data = {
                        'access': True,
                        'dates': [user_vpn_access.access_from_dttm, user_vpn_access.access_to_dttm]
                    }
                elif (user_bot_access.access_to_dttm < now_dttm()):
                    user_vpn_access_data = {
                        'access': False,
                        'dates': [user_vpn_access.access_from_dttm, user_vpn_access.access_to_dttm]
                    }
  
        user_data = DotMap({
            'user': user_tg_code,
            'user_db_data': user,
            'user_bot_access_data': user_bot_access_data,
            'user_vpn_access_data': user_vpn_access_data
        })
        return user_data


