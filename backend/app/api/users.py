from datetime import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    timezone: str
    is_verified: bool
    is_active: bool


class DigestConfigUpdate(BaseModel):
    delivery_time: time
    summary_style: str = "brief"
    is_active: bool = True


class ContentSourceCreate(BaseModel):
    source_type: str
    source_url: str
    source_name: str


class ContentSourceResponse(BaseModel):
    id: str
    source_type: str
    source_url: str
    source_name: str
    is_active: bool


class InterestProfileUpdate(BaseModel):
    keywords: str


async def get_current_user():
    return {
        "id": "mock_user_id_123",
        "email": "user@example.com",
        "timezone": "UTC",
        "is_verified": True,
        "is_active": True,
    }


@router.get("/me", response_model=UserProfile)
async def get_user_profile(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user


@router.put("/me")
async def update_user_profile(
    timezone: str, current_user: Annotated[dict, Depends(get_current_user)]
):
    return {
        "message": "Profile updated successfully (mock)",
        "user": {**current_user, "timezone": timezone},
    }


@router.get("/config")
async def get_digest_config(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "delivery_time": "07:00:00",
        "summary_style": "brief",
        "is_active": True,
        "sources": [
            {
                "id": "source_1",
                "source_type": "rss",
                "source_url": "https://feeds.ycombinator.com/ycombinator.xml",
                "source_name": "Hacker News",
                "is_active": True,
            }
        ],
        "interest_profile": {"keywords": "technology, programming, AI, startups"},
    }


@router.put("/config")
async def update_digest_config(
    config: DigestConfigUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return {
        "message": "Digest configuration updated successfully (mock)",
        "config": config.dict(),
    }


@router.post("/sources", response_model=ContentSourceResponse)
async def add_content_source(
    source: ContentSourceCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return {
        "id": "new_source_123",
        "source_type": source.source_type,
        "source_url": source.source_url,
        "source_name": source.source_name,
        "is_active": True,
    }


@router.delete("/sources/{source_id}")
async def remove_content_source(
    source_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return {"message": f"Content source {source_id} removed successfully (mock)"}


@router.put("/interest-profile")
async def update_interest_profile(
    profile: InterestProfileUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return {
        "message": "Interest profile updated successfully (mock)",
        "keywords": profile.keywords,
    }
