import uuid
import logging

from py3xui import AsyncApi, Inbound, Client
from py3xui.inbound import Inbound, Settings, Sniffing, StreamSettings
from py3xui import AsyncApi

from settings import settings

VLESS_API = AsyncApi(host=settings.XUI_HOST, username=settings.XUI_USER, password=settings.XUI_PASS)
class VlessInboundApi():
    def __init__(self, api: AsyncApi = VLESS_API):
      self.api: AsyncApi = api
      
    async def get_inbounds_data(self) -> list[dict]:
        await self.api.login()
        
        inbounds = await self.api.inbound.get_list()
        return [{'remark': inbound.remark, 'id': inbound.id, 'port': inbound.port} for inbound in inbounds]

    async def get_inbounds_id_by_remark(self, remark:str) -> int:
        await self.api.login()
        
        inbounds_data = await self.get_inbounds_data()
        for inbound in inbounds_data:
            if inbound.get('remark') == remark:
                return inbound.get('id')
        return None

    async def make_vless_inbound(self, inbound_name:str, inbound_port:int) -> int:
        await self.api.login()

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
                                                            'serverNames': ['google.com', 'www.google.com'], 
                                                            'privateKey': '6I4kzk_zJU9l7kRFlIJBOjPbaz5CLLC6Mkl222oE82w', 
                                                            'minClient': '', 
                                                            'maxClient': '', 
                                                            'maxTimediff': 0, 
                                                            'shortIds': ['1'], 
                                                            'settings': {'publicKey': 'Gy8ByVAgCO_KU78Q1jgWRjywfE5BPpTm5GNQSjrQij8', 'fingerprint': 'firefox', 'serverName': '', 'spiderX': '/'}}, 
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
                await self.api.inbound.add(inbound)
                return await self.get_inbounds_id_by_remark(remark=inbound_name)
                
            except Exception as e:
                logging.error(e)
                raise e
                      
class VlessClientApi():
    def __init__(self, api: AsyncApi = VLESS_API):
      self.api: AsyncApi = api
      
    async def make_vless_client(self, inbound_id:int, client_email:str='default') -> str:
        await self.api.login()
        
        if await self.api.client.get_by_email(client_email):
            logging.debug(f'Client: "{client_email}" already exists! Skipped!')
            return None
        else:
            client_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, client_email))
            new_client = Client(id=client_id, email=client_email, enable=True, flow='xtls-rprx-vision')
            await self.api.client.add(inbound_id=inbound_id, clients=[new_client])
            return client_email
            
    async def get_vless_client_link_by_email(self, email:str) -> str:
        await self.api.login()
        
        vless_link = ''
        client = await self.api.client.get_by_email(email)
        inbound = await self.api.inbound.get_by_id(client.inbound_id)
        for client in inbound.settings.clients:
            if client.email == email:
                cl_id = client.id
                cl_email = client.email
                cl_flow =client.flow
                ib_port = inbound.port
                ib_remark = inbound.remark
                ib_network = inbound.stream_settings.network
                ib_sec = inbound.stream_settings.security
                ib_snif = inbound.stream_settings.reality_settings["dest"].split(":")[0]
                ib_sid = inbound.stream_settings.reality_settings["shortIds"][0]
                ib_pbk = inbound.stream_settings.reality_settings["settings"]['publicKey']
                ib_fp = inbound.stream_settings.reality_settings["settings"]['fingerprint']
                ib_spx = inbound.stream_settings.reality_settings["settings"]['spiderX']
                serv_host = self.api.server.host.split('//')[1].split(':')[0]
                
                vless_link = f'vless://{cl_id}@{serv_host}:{ib_port}?type={ib_network}&security={ib_sec}&pbk={ib_pbk}&fp={ib_fp}&sni={ib_snif}&sid={ib_sid}&spx={ib_spx}&flow={cl_flow}#{ib_remark}-{cl_email}'
                return vless_link
        return ''