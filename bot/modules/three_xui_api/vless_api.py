import uuid
import logging
from datetime import datetime, timezone, timedelta

from py3xui import AsyncApi, Inbound, Client
from py3xui.inbound import Inbound, Settings, Sniffing, StreamSettings
from py3xui import AsyncApi

from settings import settings

vless_api = AsyncApi(host=settings.XUI_HOST, username=settings.XUI_USER, password=settings.XUI_PASS)

class VlessInboundApi():   
    async def get_inbounds_data(self) -> list[dict]:
        await vless_api.login()
        
        inbounds = await vless_api.inbound.get_list()
        return [{'remark': inbound.remark, 'id': inbound.id, 'port': inbound.port} for inbound in inbounds]

    async def get_inbounds_id_by_remark(self, remark:str) -> int:
        await vless_api.login()
        
        inbounds_data = await self.get_inbounds_data()
        for inbound in inbounds_data:
            if inbound.get('remark') == remark:
                return inbound.get('id')
        return None

    async def make_vless_inbound(self, inbound_name:str, inbound_port:int) -> int:
        await vless_api.login()

        if await self.get_inbounds_id_by_remark( remark=inbound_name):
            logging.debug(f'Inbound: "{inbound_name}" already exists! Skipped!')
            return -1
            
        else:
            settings=Settings(clients=[], decryption='none', fallbacks=[])
            stream_settings=StreamSettings(security='reality', 
                                        network='tcp', 
                                        tcp_settings={'acceptProxyProtocol': False, 'header': {'type': 'none'}}, 
                                        kcp_settings={}, 
                                        external_proxy=[], 
                                        reality_settings={'show': False, 
                                                            'xver': 0, 
                                                            'dest': 'google.com:443', 
                                                            'serverNames': ['www.google.com'], 
                                                            'privateKey': 'GAiJD7L8ADep2NVcQPiuZc9l_ZxXTSCXmpVzPM6CdH8', 
                                                            'minClient': '', 
                                                            'maxClient': '', 
                                                            'maxTimediff': 0, 
                                                            'shortIds': ['33cf5dbed8e1','60571c','6395f4e62e','b688d136','4b02','1d1ec1a2dc04de9e','11','db0a75113d6ea9'], 
                                                            'settings': {'publicKey': '9WIrle9cM-dmkxvaYJEeytOnkHJCYoHojVQi-zg3_DI', 'fingerprint': 'firefox', 'serverName': '', 'spiderX': '/'}}, 
                                        xtls_settings={}, 
                                        tls_settings={})
            sniffing=Sniffing(enabled=True, 
                            dest_override=['http', 'tls', 'quic', 'fakedns'], 
                            metadata_only=False, 
                            route_only=False) 
        
            inbound = Inbound(
                enable=True,
                port=inbound_port,
                protocol="vless",
                settings=settings,
                stream_settings=stream_settings,
                sniffing=sniffing,
                remark=inbound_name,
                listen='',
                total=0,
                expiry_time=0,
                client_stats=None,
                tag=('default-tag-'+inbound_name)
            )
            try:
                await vless_api.inbound.add(inbound)
                return await self.get_inbounds_id_by_remark(remark=inbound_name)
                
            except Exception as e:
                logging.error(e)
                raise e
                      
class VlessClientApi():
    async def make_vless_client(self, inbound_id:int, client_email:str) -> str:
        await vless_api.login()
        
        if await vless_api.client.get_by_email(client_email):
            logging.debug(f'Client: "{client_email}" already exists! Skipped!')
            return None
        else:
            client_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, client_email))
            exp_time = datetime.now(timezone.utc) + timedelta(30)
            new_client = Client(id=client_id, email=client_email, enable=True, flow='xtls-rprx-vision', expiryTime=int(exp_time.timestamp() * 1000))
            await vless_api.client.add(inbound_id=inbound_id, clients=[new_client])
            return client_email
    
    async def get_client_uuid_by_email(self, client_email):
        client = await vless_api.client.get_by_email(client_email)
        if client:
            inbound = await vless_api.inbound.get_by_id(client.inbound_id)
            if inbound.settings.clients:
                for client in inbound.settings.clients:
                    return client.id if client.email == client_email else None
     
    async def update_client_expired_time(self, client_email: str, new_time: datetime) -> str:
        try:
            await vless_api.login()
            client = await vless_api.client.get_by_email(client_email)
            if client:
                client_id = await self.get_client_uuid_by_email(client_email)
                
                new_client = client
                new_client.id = client_id
                new_client.expiry_time =int(new_time.timestamp() * 1000)   
                
                if client_id:
                    await vless_api.client.update(client_id, new_client)
                    return True
        except Exception as e:
            return e
            
    async def get_vless_client_link_by_email(self, email:str) -> str:
        await vless_api.login()
        
        vless_link = ''
        client = await vless_api.client.get_by_email(email)
        inbound = await vless_api.inbound.get_by_id(client.inbound_id)
        for client in inbound.settings.clients:
            if client.email == email:
                cl_id = client.id
                cl_email = client.email
                cl_flow =client.flow
                ib_port = inbound.port
                ib_remark = inbound.remark
                ib_network = inbound.stream_settings.network
                ib_sec = inbound.stream_settings.security
                ib_snif = inbound.stream_settings.reality_settings['serverNames'][0]
                ib_sid = inbound.stream_settings.reality_settings["shortIds"][0]
                ib_pbk = inbound.stream_settings.reality_settings["settings"]['publicKey']
                ib_fp = inbound.stream_settings.reality_settings["settings"]['fingerprint']
                ib_spx = inbound.stream_settings.reality_settings["settings"]['spiderX']
                serv_host = vless_api.server.host.split('//')[1].split(':')[0]
                
                vless_link = f'vless://{cl_id}@{serv_host}:{ib_port}?type={ib_network}&security={ib_sec}&pbk={ib_pbk}&fp={ib_fp}&sni={ib_snif}&sid={ib_sid}&spx={ib_spx}&flow={cl_flow}#{ib_remark}-{cl_email}'
                return vless_link
        return ''