from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated browser origins allowed to call the API",
    )
    data_dir: Path | None = Field(default=None, description="Root folder for signals and snapshots")
    catalog_path: Path | None = Field(default=None, description="Path to instruments.json")
    quote_cache_seconds: int = Field(default=4, ge=1, le=300)

    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    def resolved_data_dir(self) -> Path:
        return self.data_dir if self.data_dir is not None else REPO_ROOT / "data"

    def resolved_catalog_path(self) -> Path:
        return self.catalog_path if self.catalog_path is not None else REPO_ROOT / "config" / "instruments.json"

    def signals_dir(self) -> Path:
        return self.resolved_data_dir() / "signals"

    def scalp_signals_dir(self) -> Path:
        return self.signals_dir() / "scalp"

    def snapshots_dir(self) -> Path:
        return self.resolved_data_dir() / "snapshots"


@lru_cache
def get_settings() -> Settings:
    return Settings()
