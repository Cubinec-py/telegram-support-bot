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

    # Game Database (optional)
    GAME_DB_ENABLED: bool = False
    GAME_DB_HOST: str = "localhost"
    GAME_DB_PORT: int = 5432
    GAME_DB_NAME: str = ""
    GAME_DB_USER: str = ""
    GAME_DB_PASSWORD: str = ""

    # Bot Settings
    DEFAULT_LANGUAGE: str = "ru"
    SUPPORTED_LANGUAGES: str = "ru,en,es,uk"
    MAX_ACTIVE_TICKETS_PER_USER: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def game_database_url(self) -> str:
        if self.GAME_DB_ENABLED:
            return f"postgresql+asyncpg://{self.GAME_DB_USER}:{self.GAME_DB_PASSWORD}@{self.GAME_DB_HOST}:{self.GAME_DB_PORT}/{self.GAME_DB_NAME}"
        return ""

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

