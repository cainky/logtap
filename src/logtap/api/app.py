"""FastAPI application factory for logtap."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logtap import __version__
from logtap.api.routes import files, health, logs, parsed


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="logtap",
        description="A CLI-first log access tool for Unix systems.",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(logs.router, prefix="/logs", tags=["logs"])
    app.include_router(files.router, prefix="/files", tags=["files"])
    app.include_router(parsed.router, prefix="/parsed", tags=["parsed"])

    return app


# Create default app instance for uvicorn
app = create_app()
