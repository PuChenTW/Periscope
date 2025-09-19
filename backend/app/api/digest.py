from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class Article(BaseModel):
    title: str
    summary: str
    source_name: str
    url: str
    published_at: datetime


class DigestPreview(BaseModel):
    articles: list[Article]
    total_count: int
    generated_at: datetime


class DeliveryLogEntry(BaseModel):
    id: str
    status: str
    article_count: int | None
    error_message: str | None
    created_at: datetime


async def get_current_user():
    return {"id": "mock_user_id_123", "email": "user@example.com"}


@router.get("/preview", response_model=DigestPreview)
async def get_digest_preview(current_user: Annotated[dict, Depends(get_current_user)]):
    mock_articles = [
        {
            "title": "AI Breakthrough in Language Models",
            "summary": "Researchers have developed a new approach to training language models that reduces computational requirements by 40% while maintaining performance.",
            "source_name": "Tech News Daily",
            "url": "https://example.com/ai-breakthrough",
            "published_at": datetime.now(),
        },
        {
            "title": "Startup Funding Trends in 2024",
            "summary": "Venture capital investment patterns show a shift towards sustainable technology and healthcare startups this year.",
            "source_name": "Startup Weekly",
            "url": "https://example.com/funding-trends",
            "published_at": datetime.now(),
        },
        {
            "title": "Remote Work Best Practices",
            "summary": "New study reveals the most effective strategies for maintaining productivity and team collaboration in distributed teams.",
            "source_name": "Work & Life",
            "url": "https://example.com/remote-work",
            "published_at": datetime.now(),
        },
    ]

    return {
        "articles": mock_articles,
        "total_count": len(mock_articles),
        "generated_at": datetime.now(),
    }


@router.post("/send-now")
async def send_digest_now(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "message": "Digest generation and delivery initiated (mock)",
        "status": "queued",
        "estimated_delivery": "within 5 minutes",
    }


@router.get("/delivery-history")
async def get_delivery_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = 10,
) -> list[DeliveryLogEntry]:
    mock_history = [
        {
            "id": "delivery_1",
            "status": "delivered",
            "article_count": 5,
            "error_message": None,
            "created_at": datetime.now(),
        },
        {
            "id": "delivery_2",
            "status": "failed",
            "article_count": None,
            "error_message": "Source timeout",
            "created_at": datetime.now(),
        },
    ]

    return mock_history[:limit]


@router.get("/sources/validate")
async def validate_source(url: str):
    return {
        "url": url,
        "valid": True,
        "source_type": "rss" if "rss" in url or "feed" in url else "blog",
        "title": "Mock Source Title",
        "description": "This is a mock validation response",
    }
