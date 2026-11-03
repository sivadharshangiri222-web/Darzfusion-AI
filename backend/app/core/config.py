"""DARZFUSION AI Configuration Management."""

import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "DARZFUSION AI"
    APP_VERSION: str = "1.0.0"
    ENV: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Security & JWT
    SECRET_KEY: str = Field(
        default="darzfusion-super-secret-production-key-change-in-env-2026",
        description="Secret key used for signing JWT tokens",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./darzfusion.db",
        description="SQLAlchemy database URL. Supports sqlite:///... and postgresql://...",
    )

    # External AI: Google Gemini
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key. If empty, mock/demo fallbacks return clear error/guidance.",
    )
    DEFAULT_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Default Gemini model to use for chat and reasoning",
    )
    EMBEDDING_MODEL: str = Field(
        default="models/text-embedding-004",
        description="Google Gemini embedding model",
    )

    # Vector Storage (ChromaDB)
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default=str(BASE_DIR / "chroma_db"),
        description="Directory where ChromaDB vector data is persisted",
    )

    # File Uploads
    UPLOAD_DIR: str = Field(
        default=str(BASE_DIR / "uploads"),
        description="Directory for uploaded documents and temporary media",
    )
    MAX_UPLOAD_SIZE_MB: int = 20  # 20 MB max file size
    ALLOWED_DOCUMENT_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx"]
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".aac"]

    # Web Search Providers
    SEARCH_PROVIDER: str = Field(
        default="duckduckgo",
        description="Search provider: 'duckduckgo' (no key required), 'tavily', or 'serpapi'",
    )
    TAVILY_API_KEY: str = Field(default="")
    SERPAPI_API_KEY: str = Field(default="")

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instantiate singleton
settings = Settings()

# Ensure critical storage directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
