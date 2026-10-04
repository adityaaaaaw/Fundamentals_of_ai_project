from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Study Planner Agent"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./study_planner.db"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_REQUEST_TIMEOUT_SECONDS: float = 15.0
    FRONTEND_ORIGINS: str = "http://localhost:5173"
    DEMO_USER_ID: str = "demo-user-id"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]


settings = Settings()
