"""FastAPI dependencies for logtap."""

import secrets
from functools import lru_cache
from typing import Optional

from fastapi import Header, HTTPException, status

from logtap.models.config import Settings


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()


async def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Optional[str]:
    """
    Verify the API key if authentication is enabled.

    If LOGTAP_API_KEY is not set, authentication is disabled and all requests are allowed.
    If LOGTAP_API_KEY is set, requests must include a matching X-API-Key header.

    Args:
        x_api_key: The API key from the request header.

    Returns:
        The validated API key, or None if authentication is disabled.

    Raises:
        HTTPException: If authentication is enabled and the key is invalid.
    """
    settings = get_settings()

    # If no API key is configured, skip authentication
    if not settings.api_key:
        return None

    # API key is required but not provided
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Set X-API-Key header.",
        )

    # Use timing-safe comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    return x_api_key
