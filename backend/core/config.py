"""
NEXUS — Application configuration.
Loads all runtime settings from environment variables / .env file
using pydantic-settings. Import `settings` anywhere in the app.
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "NEXUS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # ── Security ─────────────────────────────────────────
    SECRET_KEY: str = Field(..., min_length=16)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── PostgreSQL ───────────────────────────────────────
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def use_async_postgres_driver(cls, v: str) -> str:
        if not isinstance(v, str):
            return v

        # Render provides a plain postgres/postgresql URL, but the app uses
        # SQLAlchemy's async engine and installs asyncpg, not psycopg2.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ── Redis ────────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Neo4j ────────────────────────────────────────────
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j"

    # ── Celery ───────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # ── AI ───────────────────────────────────────────────
    # AI_PROVIDER selects which backend ai_engine.py talks to:
    #   "anthropic" — paid, pay-per-token, best quality (needs ANTHROPIC_API_KEY)
    #   "gemini"    — Google's Gemini API free tier, no cost, needs GEMINI_API_KEY
    #                 (free, no card required — console.cloud.google.com/apis or
    #                 aistudio.google.com/apikey)
    #   "ollama"    — fully local, $0 forever, no signup, no rate limits, needs
    #                 Ollama running locally with a model pulled (e.g. `ollama pull llama3.1`)
    AI_PROVIDER: str = "ollama"

    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "claude-sonnet-4-6"
    AI_MAX_TOKENS: int = 4096
    AI_RATE_LIMIT_PER_MIN: int = 20

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1"

    # ── External services ────────────────────────────────
    SHODAN_API_KEY: str = ""

    # ── CORS ─────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def split_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Storage ──────────────────────────────────────────
    UPLOAD_DIR: str = "/data/uploads"
    REPORT_DIR: str = "/data/reports"
    LOG_DIR: str = "/data/logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

