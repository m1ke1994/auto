from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)
    APP_ENV: str = "production"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_SEO: str = "gpt-5-mini"
    OPENAI_MODEL_CONVERSION: str = "gpt-5-mini"
    AI_RECOMMENDATIONS_ENABLED: bool = True
    CORE_SERVICE_TOKEN: str = ""
    AI_RECOMMENDATIONS_SIGNING_SECRET: str = ""
    CORE_ALLOWED_IPS: str = ""
    SERVICE_PUBLIC_URL: str = ""
    DATABASE_URL: str = "postgresql+psycopg://ai_recommendations:password@postgres:5432/ai_recommendations"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    REQUEST_TIMEOUT_SECONDS: int = 120
    OPENAI_TIMEOUT_SECONDS: int = 120
    MAX_RETRIES: int = Field(3, ge=0, le=10)
    JOB_RETENTION_DAYS: int = 30
    MAX_REQUEST_BODY_SIZE: int = 1_048_576
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @property
    def allowed_ips(self) -> tuple[str, ...]:
        return tuple(part.strip() for part in self.CORE_ALLOWED_IPS.split(",") if part.strip())

    @property
    def ready(self) -> bool:
        return bool(
            self.CORE_SERVICE_TOKEN
            and self.AI_RECOMMENDATIONS_SIGNING_SECRET
            and self.DATABASE_URL
            and (self.OPENAI_API_KEY or not self.AI_RECOMMENDATIONS_ENABLED)
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
