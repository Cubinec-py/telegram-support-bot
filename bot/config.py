from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Telegram Bot
    BOT_TOKEN: str
    ADMIN_IDS: str

    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Bot Settings
    DEFAULT_LANGUAGE: str = "ru"
    SUPPORTED_LANGUAGES: str = "ru,en,es,uk"
    MAX_ACTIVE_TICKETS_PER_USER: int = 3
    AUTO_CLOSE_TIMEOUT: int = 60  # minutes of inactivity before a ticket is auto-closed
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def admin_ids_list(self) -> List[int]:
        return [int(id_) for id_ in self.ADMIN_IDS.split(",") if id_.strip()]

    @property
    def supported_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(",")]



settings = Settings()

