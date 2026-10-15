from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FreshBite API"
    secret_key: str = "development-only-change-me-change-this-key"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite+aiosqlite:///./freshbite.db"
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    auto_create_tables: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
