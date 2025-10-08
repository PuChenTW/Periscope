# Content Processing Architecture

## 1. RSS Feed Fetching Layer (✅ IMPLEMENTED)

Complete implementation of RSS 2.0 and Atom 1.0 feed parsing with comprehensive error handling and content extraction capabilities.

### Key Components

#### Base Fetcher Interface
Abstract class defining standard fetcher methods for validation, content fetching, and metadata extraction.

**Interface Methods:**
- `validate(url: str) -> bool`: Check if URL is accessible and valid
- `fetch_content(url: str) -> List[Article]`: Fetch and parse articles
- `get_feed_metadata(url: str) -> FeedMetadata`: Extract feed information

#### RSS/Atom Parser
Full-featured parser supporting both feed formats with graceful handling of malformed content.

**Supported Formats:**
- RSS 2.0
- Atom 1.0
- Graceful degradation for mixed/malformed feeds

**Features:**
- Automatic format detection
- Content cleaning and normalization
- Metadata extraction (title, author, published date)
- HTML tag stripping from content
- Character encoding handling

#### Factory Pattern
Automatic fetcher selection based on URL scheme and content type detection.

**Factory Features:**
- URL scheme-based selection (http/https → RSS fetcher)
- Content-type detection
- Extensible for new fetcher types
- Centralized fetcher instantiation

#### HTTP Client
Simplified async client with streamlined retry logic, native aiohttp exception handling, and connection lifecycle management.

**Key Features:**
- Async/await with aiohttp
- Native aiohttp exception handling (ClientResponseError, TimeoutError, ClientError)
- Simplified retry logic with fixed delay backoff
- Configurable timeouts
- Connection pooling
- User-agent headers

#### URL Validation
Comprehensive validation utilities for feed URLs and health checking.

**Validation Features:**
- URL format validation
- Scheme validation (http/https)
- Domain validation
- Accessibility checks
- Feed format validation

### Features

- **Format Support**: RSS 2.0 and Atom 1.0 using feedparser library
- **Error Handling**: Simplified using native aiohttp exceptions (ClientResponseError, TimeoutError, ClientError)
- **Unified Exception Handling**: Consolidated retry logic for better maintainability
- **Content Processing**: Cleaning and text normalization
- **Metadata Extraction**: Author, tags, publish dates, feed info
- **Retry Policies**: Streamlined with fixed delay backoff for predictable behavior
- **Testing**: Comprehensive suite with 73 passing tests covering unit, integration, and edge cases

## 2. AI Provider Abstraction (✅ IMPLEMENTED)

Pluggable AI model architecture enabling easy switching between different AI providers.

### Key Components

#### AIProvider Protocol
Interface defining the `create_agent()` method for provider implementations.

**Protocol Definition:**
```python
class AIProvider(Protocol):
    def create_agent(
        self,
        output_type: Type[T],
        system_prompt: str
    ) -> Agent[None, T]:
        ...
```

#### GeminiProvider
Implementation for Google Gemini models with PydanticAI integration.

**Features:**
- Integration with Google Gemini API
- Configurable model selection
- API key management
- Structured output via Pydantic models

#### OpenAIProvider
Placeholder for future OpenAI integration.

**Planned Features:**
- OpenAI API integration
- Multiple model support (GPT-4, GPT-3.5)
- Function calling support

#### Factory Function
`create_ai_provider()` for configuration-driven provider instantiation.

**Usage:**
```python
provider = create_ai_provider()  # Reads from config
agent = provider.create_agent(OutputModel, system_prompt)
```

### Features

- **Protocol-based Design**: Easy extensibility for new providers
- **Configuration-driven**: Select provider via `AI_PROVIDER` environment variable
- **Dependency Injection**: Enhanced testability with mocked providers
- **Easy Extension**: Add new providers (Anthropic, Cohere, etc.) by implementing protocol
- **Testing**: All 17 similarity detector tests passing with mock provider

### Implementation Details

- **Location**: `app/processors/ai_provider.py`
- **Usage**: Used by SimilarityDetector and TopicExtractor for AI operations
- **Lifecycle**: Provider instances created once and reused
- **Testing**: Mock provider interface for deterministic unit testing

## 3. Similarity Detection & Grouping Engine (✅ IMPLEMENTED)

AI-powered semantic analysis to detect and group similar articles from different sources using the AI provider abstraction.

### Key Features

- **AI-Powered Analysis**: Uses configurable AI providers via abstraction layer
- **Pairwise Comparison**: Compares articles for semantic similarity
- **Structured Output**: AI returns similarity score and reasoning
- **Connected Components**: Efficient grouping algorithm for similar articles
- **Topic Aggregation**: Combines topics from all articles in groups (from Article.ai_topics)
- **Caching**: Redis caching with 24-hour TTL to avoid redundant AI calls
- **Configurable Threshold**: Default similarity threshold of 0.7
- **Error Handling**: Graceful fallback behavior on AI failures
- **Testing**: Comprehensive suite with 21 passing tests

### Algorithm

1. Extract article pairs for comparison
2. For each pair, call AI to determine similarity
3. Build similarity graph from AI responses
4. Use connected components to find article groups
5. Aggregate topics from all articles in each group
6. Return grouped articles with combined topics

### Configuration

- `SIMILARITY_THRESHOLD`: Minimum confidence score (default: 0.7)
- `SIMILARITY_CACHE_TTL_MINUTES`: Cache duration (default: 1440 = 24 hours)

## 4. Topic Extraction Service (✅ IMPLEMENTED)

AI-powered topic identification for article categorization and relevance scoring.

### Key Features

- **AI-Powered Extraction**: Uses configurable AI providers
- **Multi-Topic Support**: Extracts 3-5 key topics per article
- **Structured Output**: TopicExtractionResult Pydantic model
- **Configurable Limit**: Max topics via TOPIC_EXTRACTION_MAX_TOPICS
- **Content Truncation**: 1000 character limit for efficient token usage
- **Error Handling**: Graceful fallback to empty list
- **Article Integration**: ai_topics field in Article model
- **Testing**: Comprehensive suite with 19 passing tests

### Topic Extraction Process

1. Truncate article content to 1000 characters
2. Send content to AI with extraction prompt
3. AI identifies key topics/themes
4. Parse structured response into TopicExtractionResult
5. Store topics in Article.ai_topics field
6. Use topics for relevance scoring and grouping

### Configuration

- `TOPIC_EXTRACTION_MAX_TOPICS`: Maximum topics per article (default: 5)

### Integration Points

- Called during content processing pipeline
- Topics stored in Article model
- Used by similarity detector for grouping
- Used by relevance scorer for personalization

## 5. Processing Pipeline (Planned for Phase 2)

Chain of responsibility pattern for content processing stages: validation, topic extraction (✅ complete), similarity detection (✅ complete), summarization, and personalization.

### Pipeline Stages

1. **Validation**: Check content quality and completeness
2. **Topic Extraction** (✅): Identify key themes and topics
3. **Similarity Detection** (✅): Group similar articles
4. **Summarization** (planned): Generate concise summaries
5. **Personalization** (planned): Score relevance to user interests

### Design Principles

- Each processor transforms content before passing to next stage
- Modular and testable processing components
- Error handling at each stage with fallback behavior
- Parallel processing where possible
- State management between stages

### Implementation Status

- ✅ Topic Extraction: Fully implemented and tested
- ✅ Similarity Detection: Fully implemented and tested
- ⏳ Summarization: Planned for Phase 2
- ⏳ Personalization: Planned for Phase 2
- ⏳ Pipeline Orchestration: Planned for Phase 2

## Testing Coverage

Total comprehensive tests across all content processing components: ~149 tests

### By Component

- **RSS Feed Processing**: 73 tests (simplified HTTP client, URL validation, RSS/Atom parsing, factory pattern, unified error handling)
- **Similarity Detection**: 21 tests (mock AI provider, grouping logic, topic aggregation, caching)
- **Topic Extraction**: 19 tests (topic extraction, error handling, content validation, max topics)
- **AI Provider**: Covered in dependent component tests (17+ tests using mock provider)

### Test Categories

- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: Component interaction testing
- **Edge Cases**: Error conditions, malformed input, timeout scenarios
- **Mock AI Testing**: Deterministic testing without real AI API calls
