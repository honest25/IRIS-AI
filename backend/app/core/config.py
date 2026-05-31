from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "IRIS AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | production

    # ─── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24       # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30               # 30 days
    ENCRYPTION_KEY: str = ""                          # Fernet key (set in .env)
    ALGORITHM: str = "HS256"

    # ─── Database ───────────────────────────────────────────────────────────────
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "iris"
    POSTGRES_PASSWORD: str = "iris_pass"
    POSTGRES_DB: str = "iris_db"

    # Allow DATABASE_URL to be set directly via env var
    DATABASE_URL: str | None = None

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── Redis ──────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── AI Providers ───────────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Model priority list (all free tier on OpenRouter)
    PRIMARY_MODEL: str = "openrouter/deepseek/deepseek-chat"
    FALLBACK_MODELS: List[str] = [
        "openrouter/qwen/qwen-2.5-72b-instruct",
        "openrouter/mistralai/mistral-7b-instruct",
        "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        "openrouter/google/gemma-2-9b-it:free",
    ]

    # ─── CORS ───────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "*", # Allow wildcard for Vercel deployment preview
    ]

    # ─── Gmail OAuth2 ───────────────────────────────────────────────────────────
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/v1/email/callback"

    # ─── ChromaDB ───────────────────────────────────────────────────────────────
    CHROMA_PERSIST_PATH: str = "./memory_data"
    CHROMA_COLLECTION: str = "iris_memory"

    # ─── Feature Flags ──────────────────────────────────────────────────────────
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_EMAIL: bool = False   # Set True after configuring Gmail OAuth2
    MAX_CONVERSATION_HISTORY: int = 20  # messages to include in LLM context

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
