"""Configuration settings for logtap."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables are prefixed with LOGTAP_ (e.g., LOGTAP_API_KEY).
    """

    model_config = SettingsConfigDict(
        env_prefix="LOGTAP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Log directory configuration
    log_directory: str = "/var/log"
    testing: bool = False

    # Authentication
    api_key: Optional[str] = None

    # Query defaults
    default_limit: int = 50
    max_limit: int = 1000

    def get_log_directory(self) -> str:
        """Get the log directory. Uses log_directory setting directly."""
        return self.log_directory
