from fastapi import Request
from sqlmodel.ext.asyncio.session import AsyncSession


def get_db_session(request: Request) -> AsyncSession:
    """Get the current ORM session from the middleware"""
    assert request.state.db_session is not None, "Session is not initialized"
    return request.state.db_session
