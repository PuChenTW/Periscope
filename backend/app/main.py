from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger

from app.api import auth, digest, health, users
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for Personal Daily Reading Digest",
        version="0.1.0",
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(digest.router, prefix="/digest", tags=["digest"])

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Personal Daily Reading Digest Backend")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down Personal Daily Reading Digest Backend")

    return app


app = create_app()
