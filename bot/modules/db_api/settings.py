class Settings():
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    
    @property
    def DB_URL_asyncpg(self) -> str:
        return 'postgresql+asyncpg://admin:12345678@localhost:2345/db'
    
    @property
    def DB_URL_psycopg(self) -> str:
        return 'postgresql+psycopg2://admin:12345678@localhost:2345/db'
    
    @property
    def DB_main_schema_name(self) -> str:
        return 'main'
    
    @property
    def DB_write_logs(self) -> str:
        return True
    
settings = Settings()