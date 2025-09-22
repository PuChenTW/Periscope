from fastapi import Request
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import create_db_session


class ORMSessionMiddleware(BaseHTTPMiddleware):
    """Setup the initialized ORM session for each request"""

    async def dispatch(self, request: Request, call_next):
        session = self.patchable_session()

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
        finally:
            await session.close()

    def patchable_session(self) -> AsyncSession:
        return create_db_session()
