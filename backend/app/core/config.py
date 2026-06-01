from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Support + Sales Copilot"
    app_version: str = "1.0.0"
    app_env: str = "development"
    enable_api_docs: bool = True
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    default_company_id: str = "startup-demo-001"
    default_answer_mode: str = "sales"
    admin_api_key: str | None = None
    chat_api_key: str | None = None
    require_company_id: bool = True
    max_chat_history_messages: int = 12
    max_chat_message_length: int = 4000
    max_upload_size_bytes: int = 10 * 1024 * 1024
    website_scrape_max_pages: int = 6
    website_scrape_timeout_seconds: float = 10.0
    website_scrape_user_agent: str = "AI-Support-Sales-Copilot/1.0"
    trusted_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "testserver"])
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    @field_validator("trusted_hosts", mode="before")
    @classmethod
    def normalize_trusted_hosts(cls, value):
        if value in (None, "", []):
            return ["localhost", "127.0.0.1", "testserver"]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
GROQ_API_KEY = settings.groq_api_key
GROQ_MODEL = settings.groq_model

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
