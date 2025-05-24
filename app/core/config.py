from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    PROJECT_NAME: str = "Mahjong Game API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "mcr_masters"

    JWT_SECRET_KEY: str = "secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3

    GOOGLE_CLIENT_ID: str = "secret"
    GOOGLE_CLIENT_SECRET: str = "secret"
    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    # GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/login/google/callback"
    GOOGLE_REDIRECT_URI: str = (
        "https://mcrs.duckdns.org/core/api/v1/auth/login/google/callback"
    )

    # GAME_SERVER_URL: str = "http://localhost:8001"
    GAME_SERVER_URL: str = "http://mcrs.duckdns.org:8001/"
    AGENT_SERVER_URL: str = "http://mcrs.duckdns.org:8002/"

    @property
    def sync_database_uri(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_test_settings() -> Settings:
    return Settings()


settings = get_settings()
