from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger

from app.api import auth, digest, health, users
from app.config import settings
from app.middlewares import ORMSessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    logger.info("Starting Personal Daily Reading Digest Backend")
    yield
    logger.info("Shutting down Personal Daily Reading Digest Backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for Personal Daily Reading Digest",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    app.add_middleware(ORMSessionMiddleware)

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(digest.router, prefix="/digest", tags=["digest"])

    return app
