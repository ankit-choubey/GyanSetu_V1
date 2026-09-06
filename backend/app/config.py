from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GyanSetu"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./gyansetu.db"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def model_post_init(self, __context: object) -> None:
        if self.environment.lower() in {"production", "prod"} and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
