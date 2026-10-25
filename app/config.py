from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
@lru_cache
def getInstance():
    return Settings()

settings = Settings()