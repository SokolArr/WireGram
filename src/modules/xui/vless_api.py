import uuid
from datetime import datetime, timezone, timedelta

from py3xui import AsyncApi, Inbound, Client
from py3xui.inbound import Settings, Sniffing, StreamSettings
from settings import settings
from logger import MainLogger

vless_api = AsyncApi(
    host=settings.XUI_HOST,
    username=settings.XUI_USER,
    password=settings.XUI_PASS,
)
logger = MainLogger(__name__).get()


class VlessInboundApi:
    """A class to manage VLESS inbound configurations on the X-UI panel."""

    async def get_inbounds_data(self) -> list[dict]:
        """
        Retrieve a list of all inbounds with their details.

        Returns:
            list[dict]: A list of dictionaries containing inbound details (remark, id, port).
        """
        await vless_api.login()

        inbounds = await vless_api.inbound.get_list()
        return [
            {"remark": inbound.remark, "id": inbound.id, "port": inbound.port}
            for inbound in inbounds
        ]

    async def get_inbounds_free_port(self) -> list[dict]:
        await vless_api.login()

        inbounds = await vless_api.inbound.get_list()

        all_existed_ports = []
        max_port = settings.XUI_VLESS_PORT + settings.XUI_MAX_USED_PORTS
        for inbound in inbounds:
            if (
                inbound.port >= settings.XUI_VLESS_PORT
                and inbound.port <= max_port
            ):
                all_existed_ports.append(inbound.port)

        range_vless_ports = range(settings.XUI_VLESS_PORT, max_port + 1)
        free_ports = []
        for port in range_vless_ports:
            if port not in all_existed_ports:
                free_ports.append(port)

        if free_ports:
            free_port = min(free_ports)
            if (free_port >= settings.XUI_VLESS_PORT) and (
                free_port <= max_port
            ):
                return free_port
            else:
                logger.error("NO FREE PORTS FOR VLESS CONF")
                raise Exception("NO FREE PORTS FOR VLESS CONF")
        else:
            logger.error("NO FREE PORTS FOR VLESS CONF")
            raise Exception("NO FREE PORTS FOR VLESS CONF")

    async def get_inbounds_id_by_remark(self, remark: str) -> int:
        """
        Get the ID of an inbound by its remark (name).

        Args:
            remark (str): The remark (name) of the inbound.

        Returns:
            int: The ID of the inbound if found, otherwise None.
        """
        await vless_api.login()

        inbounds_data = await self.get_inbounds_data()
        for inbound in inbounds_data:
            if inbound.get("remark") == remark:
                return inbound.get("id")
        return None

    async def make_vless_inbound(
        self, inbound_name: str, inbound_port: int
    ) -> int:
        """
        Create a new VLESS inbound with the specified name and port.

        Args:
            inbound_name (str): The name (remark) of the new inbound.
            inbound_port (int): The port number for the new inbound.

        Returns:
            int: The ID of the newly created inbound
        """
        await vless_api.login()

        inbound_id = await self.get_inbounds_id_by_remark(remark=inbound_name)

        if inbound_id:
            logger.debug(f'Inbound: "{inbound_name}" already exists! Skipped!')
            return inbound_id

        else:
            settings = Settings(clients=[], decryption="none", fallbacks=[])
            stream_settings = StreamSettings(
                security="reality",
                network="tcp",
                tcp_settings={
                    "acceptProxyProtocol": False,
                    "header": {"type": "none"},
                },
                kcp_settings={},
                external_proxy=[],
                reality_settings={
                    "show": False,
                    "xver": 0,
                    "dest": "google.com:443",
                    "serverNames": ["www.google.com"],
                    "privateKey": "GAiJD7L8ADep2NVcQPiuZc9l_ZxXTSCXmpVzPM6CdH8",
                    "minClient": "",
                    "maxClient": "",
                    "maxTimediff": 0,
                    "shortIds": [
                        "33cf5dbed8e1",
                        "60571c",
                        "6395f4e62e",
                        "b688d136",
                        "4b02",
                        "1d1ec1a2dc04de9e",
                        "11",
                        "db0a75113d6ea9",
                    ],
                    "settings": {
                        "publicKey": "9WIrle9cM-dmkxvaYJEeytOnkHJCYoHojVQi-zg3_DI",
                        "fingerprint": "firefox",
                        "serverName": "",
                        "spiderX": "/",
                    },
                },
                xtls_settings={},
                tls_settings={},
            )
            sniffing = Sniffing(
                enabled=True,
                dest_override=["http", "tls", "quic", "fakedns"],
                metadata_only=False,
                route_only=False,
            )

            inbound = Inbound(
                enable=True,
                port=inbound_port,
                protocol="vless",
                settings=settings,
                stream_settings=stream_settings,
                sniffing=sniffing,
                remark=inbound_name,
                listen="",
                total=0,
                expiry_time=0,
                client_stats=None,
                tag=("default-tag-" + inbound_name),
            )
            try:
                await vless_api.inbound.add(inbound)
                inbound_id = await self.get_inbounds_id_by_remark(
                    remark=inbound_name
                )
                await VlessClientApi(
                    expired_deltatime_days=9999
                ).make_vless_client(inbound_id, "admin_user")
                return inbound_id

            except Exception as e:
                logger.error(e)
                raise e


class VlessClientApi:
    """A class to manage VLESS client configurations on the X-UI panel."""

    def __init__(
        self, flow: str = "xtls-rprx-vision", expired_deltatime_days: int = 30
    ):
        """
        Initialize the VlessClientApi.

        Args:
            flow (str): The flow type for the client (default: 'xtls-rprx-vision').
            expired_deltatime_days (int): The number of days until the client expires (default: 30).
        """
        self.expired_deltatime_days = expired_deltatime_days
        self.flow = flow

    async def make_vless_client(
        self, inbound_id: int, client_email: str
    ) -> str:
        """
        Create a new VLESS client for the specified inbound.

        Args:
            inbound_id (int): The ID of the inbound to which the client will be added.
            client_email (str): The email address of the client.

        Returns:
            str: The email of the newly created client, or None if it already exists.
        """
        await vless_api.login()

        client = await vless_api.client.get_by_email(client_email)
        if client:
            logger.debug(f'Client: "{client_email}" already exists! Skipped!')
            return client_email
        else:
            client_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, client_email))
            exp_time = datetime.now(timezone.utc) + timedelta(
                self.expired_deltatime_days
            )
            new_client = Client(
                id=client_id,
                email=client_email,
                enable=True,
                flow=self.flow,
                expiryTime=int(exp_time.timestamp() * 1000),
            )
            await vless_api.client.add(
                inbound_id=inbound_id, clients=[new_client]
            )
            return client_email

    async def get_client_uuid_by_email(self, client_email):
        """
        Retrieve the UUID of a client by their email.

        Args:
            client_email (str): The email address of the client.

        Returns:
            str: The UUID of the client if found, otherwise None.
        """
        await vless_api.login()
        client = await vless_api.client.get_by_email(client_email)
        if client:
            inbound = await vless_api.inbound.get_by_id(client.inbound_id)
            if inbound.settings.clients:
                for client in inbound.settings.clients:
                    if client.email == client_email:
                        return client.id

    async def get_client_expired_datetime_by_email(self, client_email):
        """
        Retrieve the UUID of a client by their email.

        Args:
            client_email (str): The email address of the client.

        Returns:
            str: The UUID of the client if found, otherwise None.
        """
        await vless_api.login()
        client = await vless_api.client.get_by_email(client_email)
        if client:
            inbound = await vless_api.inbound.get_by_id(client.inbound_id)
            if inbound.settings.clients:
                for client in inbound.settings.clients:
                    if client.email == client_email:
                        return datetime.fromtimestamp(
                            client.expiry_time / 1000
                        )

    async def update_client_expired_time(
        self, client_email: str, new_time: datetime
    ) -> bool:
        """
        Update the expiration time of a client.

        Args:
            client_email (str): The email address of the client.
            new_time (datetime): The new expiration time.

        Returns:
            str: True if the update was successful, otherwise raises an exception.
        """
        try:
            await vless_api.login()
            client = await vless_api.client.get_by_email(client_email)
            if client:
                client_id = await self.get_client_uuid_by_email(client_email)

                new_client = client
                new_client.id = client_id
                new_client.flow = self.flow
                new_client.enable = True
                new_client.expiry_time = int(new_time.timestamp() * 1000)

                if client_id:
                    await vless_api.client.update(client_id, new_client)
                    return True
        except Exception as e:
            raise e

    async def delete_client(self, client_email: str) -> str:
        """
        Delete a client by their email.

        Args:
            client_email (str): The email address of the client.

        Returns:
            str: None if successful, otherwise raises an exception.
        """
        try:
            await vless_api.login()
            client = await vless_api.client.get_by_email(client_email)
            if client:
                client_inbound = await vless_api.client.get_by_email(
                    client_email
                )
                client_id = await self.get_client_uuid_by_email(client_email)
                await vless_api.client.delete(
                    client_inbound.inbound_id, client_id
                )
        except Exception as e:
            raise e

    async def get_vless_client_link_by_email(self, email: str) -> str:
        """
        Generate a VLESS connection link for a client by their email.

        Args:
            email (str): The email address of the client.

        Returns:
            str: The VLESS connection link.
        """
        await vless_api.login()

        vless_link = ""
        client = await vless_api.client.get_by_email(email)
        if client:
            inbound = await vless_api.inbound.get_by_id(client.inbound_id)
            if inbound:
                for client in inbound.settings.clients:
                    if client.email == email:
                        cl_id = client.id
                        cl_email = client.email
                        cl_flow = client.flow
                        ib_port = inbound.port
                        ib_remark = inbound.remark
                        ib_network = inbound.stream_settings.network
                        ib_sec = inbound.stream_settings.security
                        ib_snif = inbound.stream_settings.reality_settings[
                            "serverNames"
                        ][0]
                        ib_sid = inbound.stream_settings.reality_settings[
                            "shortIds"
                        ][0]
                        ib_pbk = inbound.stream_settings.reality_settings[
                            "settings"
                        ]["publicKey"]
                        ib_fp = inbound.stream_settings.reality_settings[
                            "settings"
                        ]["fingerprint"]
                        ib_spx = inbound.stream_settings.reality_settings[
                            "settings"
                        ]["spiderX"]
                        serv_host = vless_api.server.host.split("//")[1].split(
                            ":"
                        )[0]

                        vless_link = (
                            f"vless://{cl_id}@{serv_host}:{ib_port}?type={ib_network}&security={ib_sec}&pbk={ib_pbk}&"
                            f"fp={ib_fp}&sni={ib_snif}&sid={ib_sid}&spx={ib_spx}&flow={cl_flow}#{ib_remark}-{cl_email}"
                        )
            return vless_link
