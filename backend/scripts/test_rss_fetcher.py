import asyncio
import os
import sys

# Add the project root to the python path so we can import app
# This assumes the script is located in backend/scripts/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.processors.fetchers.rss import RSSFetcher


async def main():
    # Initialize the fetcher
    fetcher = RSSFetcher()

    # Example RSS feed URL (Hacker News)
    url = "https://hnrss.org/newest"

    print(f"Fetching content from: {url}")

    # Run the async fetch_content method
    result = await fetcher.fetch_content(url)

    if result.success:
        print(f"\nSuccess! Fetched {len(result.articles)} articles.")
        print(f"Source: {result.source_info.title}")
        print("-" * 50)

        # Print the first few articles
        for i, article in enumerate(result.articles[:5], 1):
            print(f"{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   Published: {article.published_at}")
            print()
    else:
        print("\nFailed to fetch content.")
        print(f"Error: {result.error_message}")


if __name__ == "__main__":
    # This is how you run an async function in __main__
    asyncio.run(main())
