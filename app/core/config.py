from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "EVE Healthcare Backend Service"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/eve_healthcare"
    TEST_DATABASE_URL: Optional[str] = "postgresql+psycopg://postgres:postgres@localhost:5432/eve_healthcare_test"
    
    # JWT & Auth
    JWT_SECRET_KEY: str = "supersecretjwtkeyforassignmentchangethisinproduction12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Webhook
    WEBHOOK_SECRET: str = "eve_mock_webhook_secret_key_2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
