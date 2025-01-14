import logging, uuid
from pydantic import BaseModel

from modules.db_api import DbManager
from modules.db_api.manager import ReturnCodes, OrderStatus, OrderResponse, now_dttm
from modules.db_api.models import UserStruct, UserOrderStruct, UserReqAccessStruct, UserAccessStruct
from modules.three_xui_api import VlessClientApi, VlessInboundApi

dbm = DbManager()

class UserAccessDataSchema(BaseModel):
    access: bool
    dates: list
    
class UserDataSchema(BaseModel):
    user: str
    user_db_data: UserStruct | None
    user_bot_access_data: UserAccessDataSchema | None
    user_vpn_access_data: UserAccessDataSchema | None
    
    class Config: #for UserStruct, UserAccessDataSchema
        arbitrary_types_allowed = True
            
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
                    user_bot_access_data = UserAccessDataSchema(
                        access = True,
                        dates = [user_bot_access.access_from_dttm, user_bot_access.access_to_dttm]
                    )
                elif (user_bot_access.access_to_dttm < now_dttm()):
                    user_bot_access_data = UserAccessDataSchema(
                        access = False,
                        dates = [user_bot_access.access_from_dttm, user_bot_access.access_to_dttm]
                    )
                    
            # VPN access:
            user_vpn_access = await dbm.get_access_by_user_id_access_name(user.user_id, 'VPN')
            if user_vpn_access:
                
                if (user_vpn_access.access_from_dttm <= now_dttm()) and (user_vpn_access.access_to_dttm > now_dttm()):
                    user_vpn_access_data = UserAccessDataSchema(
                        access = True,
                        dates = [user_vpn_access.access_from_dttm, user_vpn_access.access_to_dttm]
                    )
                elif (user_bot_access.access_to_dttm < now_dttm()):
                    user_vpn_access_data = UserAccessDataSchema(
                        access = False,
                        dates = [user_vpn_access.access_from_dttm, user_vpn_access.access_to_dttm]
                    )
        user_data = UserDataSchema(
            user = user_tg_code,
            user_db_data = user,
            user_bot_access_data = user_bot_access_data,
            user_vpn_access_data = user_vpn_access_data
        )
        return user_data
    
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
    
    async def make_order(self):
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            order_hash = str(user.user_tg_code) + now_dttm().strftime('%Y%m%d%H%M%S')
            new_order: UserOrderStruct = await dbm.get_new_order_by_user_id(user.user_id)
            if new_order:
                return OrderResponse.NEW_ORDER_EXIST
            elif await dbm.get_payed_order_by_user_id(user.user_id):
                return OrderResponse.PAYED_ORDER_EXIST
            else:
                order = UserOrderStruct(
                    order_id =  uuid.uuid5(uuid.NAMESPACE_DNS, order_hash),
                    order_status = OrderStatus.NEW.value,
                    user_id = user.user_id,
                    order_payload = f'hash: {order_hash}'
                )
                return_code = await dbm.add_order(order)
                if return_code == ReturnCodes.SUCCESS:
                    return OrderResponse.SUCCESS
                else:
                    return OrderResponse.BAD_TRY
            
    async def make_new_order_pay(self):
        user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
        if user:
            new_order: UserOrderStruct = await dbm.get_new_order_by_user_id(user.user_id)
            if new_order:
                order = UserOrderStruct(
                    order_id = new_order.order_id,
                    order_status = OrderStatus.PAYED.value
                )
                return_code = await dbm.update_order(order)
                if return_code == ReturnCodes.SUCCESS:
                    return OrderResponse.SUCCESS
                else:
                    return OrderResponse.BAD_TRY   
            elif await dbm.get_payed_order_by_user_id(user.user_id):
                return OrderResponse.PAYED_ORDER_EXIST 
            else: 
                return OrderResponse.NEW_ORDER_NF
       
    async def get_order(self):
            user: UserStruct = await dbm.get_user_by_tg_code(self.user.user_tg_code)
            if user:
                new_order: UserOrderStruct = await dbm.get_last_order_by_user_id(user.user_id)
                if new_order:
                    return new_order

            
        
        
    
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

    


