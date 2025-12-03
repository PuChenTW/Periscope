"""Authentication API endpoints for user registration and login."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dtos.auth import LoginRequest, RegisterUserRequest, TokenResponse, UserAuthResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: RegisterUserRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Register a new user account with default digest configuration.

    Creates:
    - User account with hashed password
    - Default DigestConfiguration (07:00 delivery, brief style)
    - Empty InterestProfile
    """
    auth_service = AuthService(session)
    user_dto = await auth_service.register_user(user_data)

    return UserAuthResponse(
        id=user_dto.id,
        email=user_dto.email,
        timezone=user_dto.timezone,
        is_verified=user_dto.is_verified,
        is_active=user_dto.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Authenticate user and return JWT access token.

    Token must be sent in subsequent requests as:
    Authorization: Bearer <token>
    """
    auth_service = AuthService(session)
    _, token_dto = await auth_service.authenticate_user(credentials)

    return TokenResponse(access_token=token_dto.access_token)


@router.post("/verify-email")
async def verify_email():
    return {"message": "Email verification successful (mock)", "verified": True}


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    return {"message": f"Password reset email sent to {email} (mock)"}
