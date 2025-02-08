from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DEBUG_MODE: bool
    WRITE_LOGS: bool
    DEFAULT_TIMEZONE: str = "Europe/Moscow"

    BOT_TOKEN: str
    TG_ADMIN_ID: int

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    DB_WG_USER: str = "wiregram"
    DB_WG_PASS: str = "wiregram"

    DB_DEFAULT_SCHEMA_NAME: str = "wiregram"

    XUI_HOST: str
    XUI_USER: str
    XUI_PASS: str
    XUI_ADD_URL: str = Field("XUI_ADD_URL", validate_default=False)
    XUI_TOKEN: str = Field("XUI_TOKEN", validate_default=False)

    XUI_VLESS_REMARK: str = "vless_main"
    XUI_VLESS_PORT: int = 4000
    XUI_MAX_USED_PORTS: int = 1000

    BOT_ACCESS_EXPIRED_DELTA_DAYS: int = 365
    CONF_PAY_EXPIRED_DELTA_DAYS: int = 30
    FREE_CONF_PERIOD_DAYS: int = 7
    MAX_CONF_PER_USER: int = 2
    TG_HELP_CHAT_LINK: str = "https://t.me/+z4RCgyLfgvdkNTli"

    VLESS_APP_ANDROID_LINK: str = (
        "https://play.google.com/store/apps/details?id=com.v2raytun.android"
    )
    VLESS_APP_APPLE_LINK: str = "https://apps.apple.com/app/id6476628951"
    VLESS_APP_PC_LINK: str = "https://github.com/2dust/v2rayN/releases/"
    VLESS_APP_ALL_LINK: str = "https://vlesskey.com/download"

    @property
    def DB_ADMIN_URL_asyncpg(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DB_ADMIN_URL_psycopg(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DB_WG_USER_URL_asyncpg(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_WG_USER}:{self.DB_WG_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DB_WG_USER_URL_psycopg(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_WG_USER}:{self.DB_WG_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
