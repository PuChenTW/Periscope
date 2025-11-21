#!/usr/bin/env python
"""
Test script for AssemblyActivities.

This script demonstrates the digest assembly activity by:
1. Creating sample article groups with metadata
2. Creating relevance scores for articles
3. Running the assemble_digest activity
4. Printing the resulting digest payload
"""

import asyncio
import json
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

from app.processors.fetchers.base import Article
from app.processors.relevance_scorer import RelevanceBreakdown, RelevanceResult
from app.processors.similarity_detector import ArticleGroup
from app.temporal.activities.assembly import AssemblyActivities


def create_sample_article(
    url: str,
    title: str,
    content: str,
    source_name: str,
) -> Article:
    """Create a sample article for testing."""
    return Article(
        url=url,
        title=title,
        content=content,
        fetch_timestamp=datetime.now(UTC),
        published_at=datetime.now(UTC),
        author=source_name,
        tags=[source_name],
    )


def create_sample_groups() -> list[ArticleGroup]:
    """Create sample article groups for testing."""
    articles = [
        # Group 1: AI/ML articles
        create_sample_article(
            url="https://example.com/ai-breakthrough",
            title="Major AI Breakthrough in Natural Language Processing",
            content="Researchers have achieved significant progress in NLP using transformer models. "
            "The new approach shows 45% improvement over previous methods.",
            source_name="Tech News Daily",
        ),
        create_sample_article(
            url="https://example.com/ml-optimization",
            title="Optimizing Machine Learning Models for Production",
            content="Best practices for deploying ML models at scale. This guide covers optimization "
            "techniques, monitoring, and performance tuning.",
            source_name="ML Engineering Weekly",
        ),
        # Group 2: Web Development articles
        create_sample_article(
            url="https://example.com/web-perf",
            title="Web Performance Optimization Techniques",
            content="Comprehensive guide to improving website performance. Covers caching, compression, "
            "CDN usage, and lazy loading strategies.",
            source_name="Web Development Today",
        ),
        create_sample_article(
            url="https://example.com/react-best-practices",
            title="React Best Practices for 2024",
            content="Latest React patterns and best practices. Includes hooks, state management, "
            "component composition, and testing strategies.",
            source_name="Frontend News",
        ),
        # Group 3: Python articles
        create_sample_article(
            url="https://example.com/python-async",
            title="Async Programming in Python",
            content="Deep dive into Python's asyncio library. Learn how to write efficient "
            "concurrent code with async/await.",
            source_name="Python Weekly",
        ),
    ]

    groups = [
        ArticleGroup(
            primary_article=articles[0],
            similar_articles=[articles[1]],
            common_topics=["AI", "machine learning", "NLP"],
            group_id="group_001",
        ),
        ArticleGroup(
            primary_article=articles[2],
            similar_articles=[articles[3]],
            common_topics=["web development", "performance", "frontend"],
            group_id="group_002",
        ),
        ArticleGroup(
            primary_article=articles[4],
            similar_articles=[],
            common_topics=["python", "async", "concurrency"],
            group_id="group_003",
        ),
    ]

    return groups


def create_relevance_results(groups: list[ArticleGroup]) -> dict[str, RelevanceResult]:
    """Create relevance scores for articles."""
    results = {}

    # Score for first group (high relevance)
    results[str(groups[0].primary_article.url)] = RelevanceResult(
        relevance_score=85,
        breakdown=RelevanceBreakdown(
            keyword_score=50,
            semantic_score=25.0,
            temporal_boost=5,
            quality_boost=5,
            final_score=85,
            matched_keywords=["AI", "machine learning"],
            threshold_passed=True,
        ),
        passes_threshold=True,
        matched_keywords=["AI", "machine learning"],
    )

    results[str(groups[0].similar_articles[0].url)] = RelevanceResult(
        relevance_score=78,
        breakdown=RelevanceBreakdown(
            keyword_score=45,
            semantic_score=25.0,
            temporal_boost=5,
            quality_boost=3,
            final_score=78,
            matched_keywords=["machine learning"],
            threshold_passed=True,
        ),
        passes_threshold=True,
        matched_keywords=["machine learning"],
    )

    # Score for second group (medium relevance)
    results[str(groups[1].primary_article.url)] = RelevanceResult(
        relevance_score=62,
        breakdown=RelevanceBreakdown(
            keyword_score=40,
            semantic_score=18.0,
            temporal_boost=3,
            quality_boost=1,
            final_score=62,
            matched_keywords=["web development"],
            threshold_passed=True,
        ),
        passes_threshold=True,
        matched_keywords=["web development"],
    )

    results[str(groups[1].similar_articles[0].url)] = RelevanceResult(
        relevance_score=55,
        breakdown=RelevanceBreakdown(
            keyword_score=35,
            semantic_score=15.0,
            temporal_boost=3,
            quality_boost=2,
            final_score=55,
            matched_keywords=[],
            threshold_passed=True,
        ),
        passes_threshold=True,
        matched_keywords=[],
    )

    # Score for third group (below threshold)
    results[str(groups[2].primary_article.url)] = RelevanceResult(
        relevance_score=35,
        breakdown=RelevanceBreakdown(
            keyword_score=20,
            semantic_score=10.0,
            temporal_boost=3,
            quality_boost=2,
            final_score=35,
            matched_keywords=[],
            threshold_passed=False,
        ),
        passes_threshold=False,
        matched_keywords=[],
    )

    return results


async def main():
    """Run the assembly activity test."""
    print("=" * 80)
    print("Testing AssemblyActivities")
    print("=" * 80)

    # Create sample data
    print("\n1. Creating sample article groups...")
    groups = create_sample_groups()
    print(f"   Created {len(groups)} article groups")
    for i, group in enumerate(groups, 1):
        print(f"   - Group {i}: {group.primary_article.title} (+{len(group.similar_articles)} similar)")

    print("\n2. Creating relevance scores...")
    relevance_results = create_relevance_results(groups)
    print(f"   Created scores for {len(relevance_results)} articles")

    # Run assembly activity
    print("\n3. Running assemble_digest activity...")
    activity = AssemblyActivities()

    try:
        payload = await activity.assemble_digest(
            user_id="test_user_001",
            user_email="test@example.com",
            article_groups=groups,
            relevance_results=relevance_results,
        )

        # Display results
        print("\n4. Digest Assembly Results:")
        print(f"   User ID: {payload.user_id}")
        print(f"   Email: {payload.user_email}")
        print(f"   Generation Time: {payload.generation_timestamp}")
        print("\n   Metadata:")
        for key, value in payload.metadata.items():
            print(f"   - {key}: {value}")

        print("\n5. HTML Body Preview (first 500 chars):")
        print("   " + "-" * 76)
        preview = payload.html_body[:500]
        for line in preview.split("\n"):
            print(f"   {line}")
        if len(payload.html_body) > 500:
            print("   ...")
        print("   " + "-" * 76)

        print("\n6. Text Body Preview (first 500 chars):")
        print("   " + "-" * 76)
        preview = payload.text_body[:500]
        for line in preview.split("\n"):
            print(f"   {line}")
        if len(payload.text_body) > 500:
            print("   ...")
        print("   " + "-" * 76)

        print(f"\n7. Article Groups in Payload: {len(payload.article_groups)}")
        for i, group in enumerate(payload.article_groups, 1):
            print(f"   - Group {i}: {group.primary_article.title}")
            print(f"     Similar articles: {len(group.similar_articles)}")
            print(f"     Topics: {', '.join(group.common_topics)}")

        # Save detailed output files
        output_dir = Path(__file__).parent.parent
        json_file = output_dir / "digest_output.json"
        html_file = output_dir / "digest_output.html"
        text_file = output_dir / "digest_output.txt"

        # Save JSON summary
        output_data = {
            "payload": {
                "user_id": payload.user_id,
                "user_email": payload.user_email,
                "generation_timestamp": payload.generation_timestamp.isoformat(),
                "metadata": payload.metadata,
                "article_groups": [
                    {
                        "group_id": g.group_id,
                        "primary_title": g.primary_article.title,
                        "primary_url": str(g.primary_article.url),
                        "similar_count": len(g.similar_articles),
                        "topics": g.common_topics,
                    }
                    for g in payload.article_groups
                ],
            },
            "html_body_length": len(payload.html_body),
            "text_body_length": len(payload.text_body),
        }

        json_file.write_text(json.dumps(output_data, indent=2))
        print("\n8. Output files saved:")
        print(f"   - JSON summary: {json_file}")

        # Save HTML body
        html_file.write_text(payload.html_body)
        print(f"   - HTML body: {html_file}")

        # Save text body
        text_file.write_text(payload.text_body)
        print(f"   - Text body: {text_file}")

        print("\n✓ Assembly activity completed successfully!")

    except Exception as e:
        print(f"\n✗ Error during assembly: {e}")
        traceback.print_exc()
        return 1

    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
