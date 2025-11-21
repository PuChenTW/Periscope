# Assembly Activities Test Script

This script demonstrates and tests the `AssemblyActivities` class, which is responsible for assembling final digest payloads from processed article groups.

## Overview

The `test_assembly.py` script:

1. **Creates sample article groups** - Generates 3 article groups with realistic content covering different topics (AI/ML, Web Development, Python)
2. **Creates relevance scores** - Simulates relevance scoring results for each article with proper scoring breakdowns
3. **Runs the assemble_digest activity** - Executes the core assembly logic that:
   - Filters articles by relevance threshold
   - Sorts groups by relevance score
   - Renders HTML and plain text email templates
   - Builds metadata about the digest
4. **Displays and saves results** - Shows previews of the output and saves detailed JSON results

## Running the Script

```bash
cd backend
uv run python scripts/test_assembly.py
```

## Output

The script produces:

### Console Output

- **Section 1**: Lists all created article groups with details
- **Section 2**: Shows relevance score creation
- **Section 3**: Executes the assembly activity
- **Section 4**: Displays the generated digest metadata:
  - User ID and email
  - Generation timestamp
  - Metadata (article counts, file sizes, execution time)
- **Section 5**: HTML body preview (first 500 characters)
- **Section 6**: Plain text body preview (first 500 characters)
- **Section 7**: Lists article groups included in the final digest
- **Section 8**: Path to detailed JSON output

### File Output

The script saves three output files to the `backend/` directory:

1. **digest_output.json** - Metadata summary
2. **digest_output.html** - Full HTML email body
3. **digest_output.txt** - Full plain text email body

#### JSON Summary (digest_output.json)

```json
{
  "payload": {
    "user_id": "test_user_001",
    "user_email": "test@example.com",
    "generation_timestamp": "2025-11-13T14:37:57.159790+00:00",
    "metadata": {
      "total_groups": 2,
      "total_articles": 4,
      "html_size_bytes": 4228,
      "text_size_bytes": 1044,
      "assembly_time_ms": 6
    },
    "article_groups": [
      {
        "group_id": "group_001",
        "primary_title": "...",
        "primary_url": "...",
        "similar_count": 1,
        "topics": ["AI", "machine learning", "NLP"]
      }
    ]
  },
  "html_body_length": 4225,
  "text_body_length": 764
}
```

#### HTML Body (digest_output.html)

Complete HTML email with:
- Responsive design (works on mobile and desktop)
- Professional styling with colors and fonts
- Article groups with titles, sources, dates, and links
- Similar articles listed under each primary article
- Header with digest date
- Footer with generation timestamp

**Sample structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Reading Digest</title>
    <style>
        /* Professional email styling */
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; ... }
        ...
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 Daily Reading Digest</h1>
            <p>Thursday, November 13, 2025</p>
        </div>

        <div class="article-group">
            <!-- Article groups with related articles -->
        </div>
    </div>
</body>
</html>
```

#### Text Body (digest_output.txt)

Plain text version suitable for email clients that don't support HTML:
- Clear article grouping with separator lines
- Readable formatting with indentation for related articles
- Direct URLs for all links
- Generation timestamp

**Sample structure:**
```
DAILY READING DIGEST
Thursday, November 13, 2025

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Major AI Breakthrough in Natural Language Processing
Source: Tech News Daily
Date: 2025-11-13 14:40
Link: https://example.com/ai-breakthrough

Related Articles (1):
  • Optimizing Machine Learning Models for Production
    Source: ML Engineering Weekly
    Link: https://example.com/ml-optimization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generated at 2025-11-13 14:40:37 UTC
```

## What It Tests

The script validates:

1. **Relevance Filtering**: Articles below the threshold (score < 40) are filtered out
   - Input: 3 article groups (5 articles total)
   - Output: 2 groups (4 articles total) - the Python article is filtered because its score is 35
2. **Sorting**: Groups are sorted by highest relevance score
   - AI/ML group (score 85) appears first
   - Web Development group (score 62) appears second
3. **Template Rendering**: Both HTML and plain text templates render successfully
4. **Metadata Tracking**: Accurate counts and timing information
5. **Error Handling**: Proper exception handling during template rendering

## Key Sample Data

### Article Groups

| Group | Topic | Primary Article | Similar Articles | Relevance |
|-------|-------|-----------------|-----------------|-----------|
| 1 | AI/ML | Major AI Breakthrough in NLP | ML Model Optimization | 85/78 |
| 2 | Web Dev | Web Performance Optimization | React Best Practices | 62/55 |
| 3 | Python | Async Programming in Python | (none) | 35 (filtered) |

### Relevance Scoring

Scores are created with realistic breakdowns:
- **keyword_score**: Keyword matching (0-60)
- **semantic_score**: AI semantic analysis (0-30)
- **temporal_boost**: Freshness bonus (0-5)
- **quality_boost**: Quality assessment (0-5)
- **final_score**: Total (0-100)

## Integration with Actual Workflows

When integrating with real Temporal workflows:

```python
# In your workflow
activity = AssemblyActivities()
payload = await activity.assemble_digest(
    user_id=user_id,
    user_email=user_email,
    article_groups=grouped_articles,
    relevance_results=relevance_scores,
)
```

The returned `DigestPayload` contains:
- `html_body`: Email-ready HTML for sending
- `text_body`: Plain text version as fallback
- `article_groups`: Filtered, sorted groups for reference
- `metadata`: Processing statistics
- `generation_timestamp`: When the digest was created

## Debugging

To debug the templates, check:

1. **Template Location**: `backend/app/temporal/activities/templates/`
   - `digest.html` - HTML email template
   - `digest.txt` - Plain text email template

2. **Template Variables** (available in both):
   - `article_groups` - Sorted, filtered article groups
   - `date` - Formatted date string
   - `generated_at` - Timestamp object

3. **Common Issues**:
   - Missing template files → Check file paths in AssemblyActivities
   - Template rendering errors → Inspect HTML/text body preview in output
   - Empty article groups → Verify relevance threshold filtering

## Related Components

- **AssemblyActivities** (`app/temporal/activities/assembly.py`): Core activity implementation
- **DigestPayload** (`app/temporal/activities/assembly.py`): Output data model
- **Article** (`app/processors/fetchers/base.py`): Article model
- **ArticleGroup** (`app/processors/similarity_detector.py`): Grouped articles model
- **RelevanceResult** (`app/processors/relevance_scorer.py`): Scoring model
