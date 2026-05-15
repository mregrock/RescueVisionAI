from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RVA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "rescue-vision-ai"
    service_version: str = "0.1.0"
    log_level: str = "INFO"

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    protocols_path: Path = PROJECT_ROOT / "protocols.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
