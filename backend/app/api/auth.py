from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    timezone: str = "UTC"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    return {
        "message": "User registration successful (mock)",
        "user": {
            "email": user_data.email,
            "timezone": user_data.timezone,
            "is_verified": False,
        },
    }


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    return {"access_token": "mock_jwt_token_12345", "token_type": "bearer"}


@router.post("/verify-email")
async def verify_email(token: str):
    return {"message": "Email verification successful (mock)", "verified": True}


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    return {"message": f"Password reset email sent to {email} (mock)"}
