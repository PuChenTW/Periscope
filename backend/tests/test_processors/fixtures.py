"""
Test fixtures for RSS Feed Fetching Layer tests
"""

VALID_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test RSS Feed</title>
        <description>A test RSS feed for unit testing</description>
        <link>https://example.com</link>
        <language>en-US</language>
        <lastBuildDate>Wed, 22 Nov 2023 10:00:00 GMT</lastBuildDate>
        <generator>Test Generator</generator>

        <item>
            <title>First Test Article</title>
            <link>https://example.com/article-1</link>
            <description><![CDATA[This is the first test article with <strong>HTML</strong> content.]]></description>
            <pubDate>Wed, 22 Nov 2023 09:00:00 GMT</pubDate>
            <author>test@example.com (Test Author)</author>
            <guid>https://example.com/article-1</guid>
            <category>Technology</category>
            <category>Testing</category>
        </item>

        <item>
            <title>Second Test Article</title>
            <link>https://example.com/article-2</link>
            <description>This is the second test article without HTML.</description>
            <pubDate>Wed, 22 Nov 2023 08:00:00 GMT</pubDate>
            <author>author2@example.com</author>
            <guid>article-2-guid</guid>
        </item>

        <item>
            <title>Third Test Article</title>
            <link>https://example.com/article-3</link>
            <description>Third article for testing pagination limits.</description>
            <pubDate>Wed, 22 Nov 2023 07:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""

VALID_ATOM_FEED = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Test Atom Feed</title>
    <subtitle>A test Atom feed for unit testing</subtitle>
    <link href="https://example.com/atom.xml" rel="self"/>
    <link href="https://example.com"/>
    <id>https://example.com</id>
    <updated>2023-11-22T10:00:00Z</updated>

    <entry>
        <title>Atom Test Article</title>
        <link href="https://example.com/atom-article-1"/>
        <id>https://example.com/atom-article-1</id>
        <updated>2023-11-22T09:00:00Z</updated>
        <published>2023-11-22T09:00:00Z</published>
        <author>
            <name>Atom Author</name>
            <email>atom@example.com</email>
        </author>
        <content type="html"><![CDATA[This is an <em>Atom</em> entry with HTML content.]]></content>
        <category term="atom"/>
        <category term="testing"/>
    </entry>

    <entry>
        <title>Second Atom Article</title>
        <link href="https://example.com/atom-article-2"/>
        <id>https://example.com/atom-article-2</id>
        <updated>2023-11-22T08:00:00Z</updated>
        <summary>Summary of the second Atom article.</summary>
    </entry>
</feed>"""

MALFORMED_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Malformed RSS Feed</title>
        <description>A malformed RSS feed for error testing</description>
        <link>https://example.com</link>

        <item>
            <title>Article with missing link</title>
            <description>This article has no link tag</description>
        </item>

        <item>
            <!-- Missing title -->
            <link>https://example.com/no-title</link>
            <description>This article has no title</description>
        </item>

        <item>
            <title></title>
            <link>https://example.com/empty-title</link>
            <description>This article has empty title</description>
        </item>
    </channel>
</rss>"""

EMPTY_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Empty RSS Feed</title>
        <description>An RSS feed with no items</description>
        <link>https://example.com</link>
    </channel>
</rss>"""

INVALID_XML = """This is not valid XML at all!
<rss><channel><title>Broken"""

RSS_WITH_CONTENT_ENCODED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
        <title>RSS with Content</title>
        <description>RSS feed with content:encoded</description>
        <link>https://example.com</link>

        <item>
            <title>Article with Full Content</title>
            <link>https://example.com/full-content</link>
            <description>Short description</description>
            <content:encoded><![CDATA[
                <p>This is the full article content with <strong>HTML formatting</strong>.</p>
                <p>It includes multiple paragraphs and <a href="https://example.com">links</a>.</p>
            ]]></content:encoded>
            <pubDate>Wed, 22 Nov 2023 10:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""
