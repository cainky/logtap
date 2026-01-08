"""Health check endpoint for logtap."""

from fastapi import APIRouter

from logtap import __version__
from logtap.models.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check the health of the logtap service.

    Returns:
        Health status and version information.
    """
    return HealthResponse(status="healthy", version=__version__)
