from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import create_engine_and_session


class ORMSessionMiddleware(BaseHTTPMiddleware):
    """Setup the initialized ORM session for each request"""

    async def dispatch(self, request: Request, call_next):
        _, async_session = create_engine_and_session()
        async with async_session() as session:
            request.state.db_session = session

            try:
                response = await call_next(request)
                dirty = any(session.dirty or session.deleted or session.new)
                if dirty:
                    msg = f"session is dirty, should be committed: {session.dirty=}, {session.deleted=}, {session.new=}"
                    raise RuntimeError(msg)
                return response
            except Exception:
                await session.rollback()
                raise
