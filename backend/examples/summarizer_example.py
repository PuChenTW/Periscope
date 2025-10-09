"""
Example usage of the Summarizer module.

This script demonstrates how to use the PydanticAI Summarizer to generate
article summaries with different styles.
"""

import asyncio
from datetime import UTC, datetime

from pydantic import HttpUrl

from app.config import get_settings
from app.processors.ai_provider import create_ai_provider
from app.processors.fetchers.base import Article
from app.processors.summarizer import Summarizer


async def main():
    """Demonstrate summarizer usage with different styles."""
    print("=" * 60)
    print("PydanticAI Summarizer Example")
    print("=" * 60)

    # Create sample article
    article = Article(
        title="AI Breakthrough: New Language Model Achieves Human-Level Understanding",
        url=HttpUrl("https://example.com/ai-breakthrough"),
        content=(
            "Researchers at leading AI laboratory have announced a breakthrough in natural language "
            "processing. The new model, called DeepMind-X, demonstrates unprecedented ability to "
            "understand context, nuance, and complex reasoning. In benchmark tests, the model scored "
            "within the range of human experts across multiple domains including medicine, law, and "
            "engineering. The researchers attribute the breakthrough to novel architectural improvements "
            "and a new training methodology that emphasizes reasoning over pattern matching. Industry "
            "experts are calling this a potential turning point in AI development, with implications "
            "for everything from healthcare diagnostics to legal research. The model is expected to be "
            "released for research purposes later this year, pending further safety evaluations."
        ),
        published_at=datetime(2024, 1, 15, 10, 0),
        fetch_timestamp=datetime.now(UTC),
        tags=["AI", "DeepMind", "NLP"],
        ai_topics=["Artificial Intelligence", "Natural Language Processing", "Machine Learning"],
    )

    print("\nOriginal Article:")
    print(f"Title: {article.title}")
    print(f"Content length: {len(article.content)} characters")
    print(f"Topics: {', '.join(article.ai_topics)}")

    # Get settings
    settings = get_settings()
    print("\nSettings:")
    print(f"  Max summary length: {settings.summary_max_length} words")
    print(f"  Content sent to AI: {settings.summary_content_length} chars")

    # Create AI provider
    # Note: In real usage, this would use actual AI provider (Gemini/OpenAI)
    # For this example, we would need valid API keys
    print("\nNote: This example requires valid AI API keys to run.")
    print("The following demonstrates the API usage pattern:\n")

    # Example 1: Brief summary
    print("-" * 60)
    print("Example 1: Brief Summary")
    print("-" * 60)
    summarizer_brief = Summarizer(summary_style="brief")
    print(f"Style: {summarizer_brief.summary_style}")
    print("Usage:")
    print("  article_with_summary = await summarizer_brief.summarize(article)")
    print("  print(article_with_summary.summary)")

    # Example 2: Detailed summary
    print("\n" + "-" * 60)
    print("Example 2: Detailed Summary")
    print("-" * 60)
    summarizer_detailed = Summarizer(summary_style="detailed")
    print(f"Style: {summarizer_detailed.summary_style}")
    print("Usage:")
    print("  article_with_summary = await summarizer_detailed.summarize(article)")
    print("  print(article_with_summary.summary)")

    # Example 3: Bullet points summary
    print("\n" + "-" * 60)
    print("Example 3: Bullet Points Summary")
    print("-" * 60)
    summarizer_bullets = Summarizer(summary_style="bullet_points")
    print(f"Style: {summarizer_bullets.summary_style}")
    print("Usage:")
    print("  article_with_summary = await summarizer_bullets.summarize(article)")
    print("  print(article_with_summary.summary)")

    # Example 4: Custom configuration
    print("\n" + "-" * 60)
    print("Example 4: Custom Configuration")
    print("-" * 60)
    print("Custom settings for shorter summaries:")
    print("""
    from app.config import Settings

    custom_settings = Settings(
        database_url="postgresql://...",
        secret_key="...",
        summary_max_length=300,        # Shorter summaries
        summary_content_length=1500,   # Less content to AI
    )

    summarizer = Summarizer(
        settings=custom_settings,
        summary_style="brief"
    )
    """)

    # Example 5: Integration with pipeline
    print("\n" + "-" * 60)
    print("Example 5: Integration with Content Pipeline")
    print("-" * 60)
    print("""
    async def process_articles(articles, user_preferences):
        # Extract topics first
        topic_extractor = TopicExtractor()
        for article in articles:
            article.ai_topics = await topic_extractor.extract_topics(article)

        # Then generate summaries using user's preferred style
        summarizer = Summarizer(summary_style=user_preferences.summary_style)
        summarized_articles = []
        for article in articles:
            summarized = await summarizer.summarize(article)
            summarized_articles.append(summarized)

        return summarized_articles
    """)

    print("\n" + "=" * 60)
    print("✅ Summarizer module successfully demonstrated!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
