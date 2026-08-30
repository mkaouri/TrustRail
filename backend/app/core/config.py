from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment (prefix ``TRUSTRAIL_``)."""

    model_config = SettingsConfigDict(
        env_prefix="TRUSTRAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "local"
    log_level: str = "INFO"
    service_name: str = "trustrail"
    # Product version; single source for the /health response.
    version: str = "0.1.0"

    # Database DSNs use plain env names (no TRUSTRAIL_ prefix); never defaulted to a secret.
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    test_database_url: str | None = Field(default=None, validation_alias="TEST_DATABASE_URL")
    db_echo: bool = False

    # OPA policy engine. URL uses a plain env name; timeout is a strict fail-closed cap.
    opa_url: str | None = Field(default=None, validation_alias="OPA_URL")
    opa_timeout_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
