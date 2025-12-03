from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dtos.digest import DeliveryLogEntryResponse, DigestPreviewResponse

router = APIRouter()


async def get_current_user():
    return {"id": "mock_user_id_123", "email": "user@example.com"}


@router.get("/preview", response_model=DigestPreviewResponse)
async def get_digest_preview(current_user: Annotated[dict, Depends(get_current_user)]):  # noqa: ARG001
    mock_articles = [
        {
            "title": "AI Breakthrough in Language Models",
            "summary": "Researchers have developed a new approach to training language models that reduces computational requirements by 40% while maintaining performance.",  # noqa: E501
            "source_name": "Tech News Daily",
            "url": "https://example.com/ai-breakthrough",
            "published_at": datetime.now(UTC),
        },
        {
            "title": "Startup Funding Trends in 2024",
            "summary": "Venture capital investment patterns show a shift towards sustainable technology and healthcare startups this year.",  # noqa: E501
            "source_name": "Startup Weekly",
            "url": "https://example.com/funding-trends",
            "published_at": datetime.now(UTC),
        },
        {
            "title": "Remote Work Best Practices",
            "summary": "New study reveals the most effective strategies for maintaining productivity and team collaboration in distributed teams.",  # noqa: E501
            "source_name": "Work & Life",
            "url": "https://example.com/remote-work",
            "published_at": datetime.now(UTC),
        },
    ]

    return {
        "articles": mock_articles,
        "total_count": len(mock_articles),
        "generated_at": datetime.now(UTC),
    }


@router.post("/send-now")
async def send_digest_now(current_user: Annotated[dict, Depends(get_current_user)]):  # noqa: ARG001
    return {
        "message": "Digest generation and delivery initiated (mock)",
        "status": "queued",
        "estimated_delivery": "within 5 minutes",
    }


@router.get("/delivery-history")
async def get_delivery_history(
    current_user: Annotated[dict, Depends(get_current_user)],  # noqa: ARG001
    limit: int = 10,
) -> list[DeliveryLogEntryResponse]:
    mock_history = [
        {
            "id": "delivery_1",
            "status": "delivered",
            "article_count": 5,
            "error_message": None,
            "created_at": datetime.now(UTC),
        },
        {
            "id": "delivery_2",
            "status": "failed",
            "article_count": None,
            "error_message": "Source timeout",
            "created_at": datetime.now(UTC),
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
