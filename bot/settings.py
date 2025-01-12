from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DEBUG_MODE: bool
    WRITE_LOGS: bool
    
    BOT_TOKEN: str
    TG_ADMIN_ID: str
    
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    XUI_HOST: str
    XUI_USER: str
    XUI_PASS: str
    XUI_ADD_URL: str = Field('XUI_HOST', validate_default=False)
    XUI_TOKEN: str = Field('XUI_HOST', validate_default=False)

    @property
    def DB_URL_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def DB_URL_psycopg(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def DB_main_schema_name(self) -> str:
        return 'main'
    
    model_config = SettingsConfigDict(env_file=".env")
    
settings = Settings()