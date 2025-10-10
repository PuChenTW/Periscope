# Configuration Management

## Environment-based Configuration

Use Pydantic BaseSettings for type-safe configuration management. All configuration is loaded from environment variables with support for .env files.

### Nested Configuration Structure

The configuration uses nested Pydantic models with the `__` (double underscore) delimiter for environment variables. This provides better organization and type safety.

**Example:**
```python
# Access nested configuration in code
settings = get_settings()
database_url = settings.database.url          # From DATABASE__URL
ai_provider = settings.ai.provider            # From AI__PROVIDER
threshold = settings.similarity.threshold     # From SIMILARITY__THRESHOLD
```

**Environment Variable Format:**
- Use `__` (double underscore) to separate the group name from the field name
- Example: `DATABASE__URL` maps to `settings.database.url`
- Example: `AI__GEMINI_API_KEY` maps to `settings.ai.gemini_api_key`
- Example: `SIMILARITY__THRESHOLD` maps to `settings.similarity.threshold`

## Configuration Categories

### Database Configuration
Accessed via `settings.database.*`
- `DATABASE__URL`: PostgreSQL connection string (required)

### Redis Configuration
Accessed via `settings.redis.*`
- `REDIS__URL`: Redis connection URL (default: "redis://localhost:6379/0")
- `REDIS__MAX_CONNECTIONS`: Maximum connection pool size (default: 10)

### Cache Configuration
Accessed via `settings.cache.*`
- `CACHE__TTL_MINUTES`: Cache TTL in minutes (default: 60)

### Email Provider Configuration
Accessed via `settings.email.*`
- `EMAIL__PROVIDER`: Provider name - smtp, sendgrid, ses (default: "smtp")
- `EMAIL__API_KEY`: Provider API key (default: "")
- `EMAIL__SMTP_HOST`: SMTP server host (default: "localhost")
- `EMAIL__SMTP_PORT`: SMTP server port (default: 587)
- `EMAIL__SMTP_USERNAME`: SMTP authentication username (default: "")
- `EMAIL__SMTP_PASSWORD`: SMTP authentication password (default: "")

### AI Provider Settings
Accessed via `settings.ai.*`
- `AI__PROVIDER`: Provider selection - gemini, openai, anthropic, etc. (default: "gemini")
- `AI__GEMINI_API_KEY`: Google Gemini API key (default: "")
- `AI__GEMINI_MODEL`: Model name (default: "gemini-2.5-flash-lite")
- `AI__OPENAI_API_KEY`: OpenAI API key (default: "")
- `AI__OPENAI_MODEL`: OpenAI model name (default: "gpt-5-nano")

### RSS Fetcher Configuration
Accessed via `settings.rss.*`
- `RSS__FETCH_TIMEOUT`: Fetch timeout in seconds (default: 30)
- `RSS__MAX_RETRIES`: Maximum retry attempts (default: 3)
- `RSS__RETRY_DELAY`: Delay between retries in seconds (default: 1.0)
- `RSS__MAX_ARTICLES_PER_FEED`: Maximum articles per feed (default: 100)
- `RSS__USER_AGENT`: User agent string (default: "Periscope-Bot/1.0 (+https://periscope.ai/bot)")

### Similarity Detection Configuration
Accessed via `settings.similarity.*`
- `SIMILARITY__THRESHOLD`: Minimum confidence score for similarity (default: 0.7, range: 0.0-1.0)
- `SIMILARITY__CACHE_TTL_MINUTES`: Cache duration for similarity results (default: 1440 = 24 hours)
- `SIMILARITY__BATCH_SIZE`: Maximum article pairs to compare (default: 10)

### Topic Extraction Configuration
Accessed via `settings.topic_extraction.*`
- `TOPIC_EXTRACTION__MAX_TOPICS`: Maximum topics per article (default: 5, range: 1-10)

### Summarization Configuration
Accessed via `settings.summarization.*`
- `SUMMARIZATION__MAX_LENGTH`: Maximum words in summary (default: 500)
- `SUMMARIZATION__CONTENT_LENGTH`: Maximum content chars sent to AI for summarization (default: 2000)

### Custom Prompt Validation Configuration
Accessed via `settings.custom_prompt.*`
- `CUSTOM_PROMPT__MAX_LENGTH`: Maximum prompt length (default: 1000)
- `CUSTOM_PROMPT__MIN_LENGTH`: Minimum prompt length (default: 10)
- `CUSTOM_PROMPT__VALIDATION_ENABLED`: Enable prompt validation (default: true)

### AI Prompt Validation Configuration
Accessed via `settings.ai_validation.*`
- `AI_VALIDATION__ENABLED`: Enable AI-powered validation (default: true)
- `AI_VALIDATION__THRESHOLD`: Minimum confidence score (default: 0.8)
- `AI_VALIDATION__CACHE_TTL_MINUTES`: Cache duration (default: 1440)

### Content Normalization Configuration
Accessed via `settings.content.*`
- `CONTENT__MIN_LENGTH`: Minimum content length (default: 100)
- `CONTENT__MAX_LENGTH`: Maximum content length (default: 50000)
- `CONTENT__SPAM_DETECTION_ENABLED`: Enable spam detection (default: true)
- `CONTENT__TITLE_MAX_LENGTH`: Maximum title length (default: 500)
- `CONTENT__AUTHOR_MAX_LENGTH`: Maximum author length (default: 100)
- `CONTENT__TAG_MAX_LENGTH`: Maximum tag length (default: 50)
- `CONTENT__MAX_TAGS_PER_ARTICLE`: Maximum tags per article (default: 20)
- `CONTENT__QUALITY_SCORING_ENABLED`: Enable quality scoring (default: true)

### Personalization Configuration
Accessed via `settings.personalization.*`
- `PERSONALIZATION__KEYWORD_WEIGHT_TITLE`: Weight for title keyword matches (default: 3)
- `PERSONALIZATION__KEYWORD_WEIGHT_CONTENT`: Weight for content keyword matches (default: 2)
- `PERSONALIZATION__KEYWORD_WEIGHT_TAGS`: Weight for tag/topic keyword matches (default: 4)
- `PERSONALIZATION__MAX_KEYWORDS`: Maximum keywords per interest profile (default: 50)
- `PERSONALIZATION__RELEVANCE_THRESHOLD_DEFAULT`: Default relevance threshold for filtering (default: 40, range: 0-100)
- `PERSONALIZATION__BOOST_FACTOR_DEFAULT`: Default boost factor multiplier (default: 1.0)
- `PERSONALIZATION__CACHE_TTL_MINUTES`: Cache duration for relevance results (default: 720 = 12 hours)
- `PERSONALIZATION__ENABLE_SEMANTIC_SCORING`: Enable AI semantic scoring (default: true)

## Processor Settings Architecture

### Design Principle

Each processor class accepts only the specific settings it needs rather than the full Settings object. This architectural pattern provides:

**Clear Dependencies:**
Easy to see what configuration each processor requires. Dependencies are explicit in constructor signatures.

**Better Testability:**
Test with minimal settings objects containing only relevant configuration. No need to create full Settings objects for testing individual processors.

**Loose Coupling:**
Processors don't depend on unrelated configuration. Changes to unrelated settings don't affect processor initialization.

**Type Safety:**
Specific settings types prevent configuration errors at compile time. Wrong settings type causes immediate type checking failures.

### Settings Groups

**SimilaritySettings:**
Configuration for similarity detection and grouping engine. Controls threshold for similarity matching, cache duration for results, and batch size for comparison operations.

**TopicExtractionSettings:**
Configuration for topic extraction service. Controls maximum number of topics extracted per article.

**SummarizationSettings:**
Configuration for summary generation. Controls maximum summary length and content truncation for AI processing.

**CustomPromptSettings:**
Configuration for user-defined custom prompts. Controls prompt length limits and validation rules.

**AIPromptValidationSettings:**
Configuration for AI-powered prompt validation. Controls whether AI validation is enabled, confidence thresholds, and cache duration.

**ContentNormalizationSettings:**
Comprehensive configuration for content validation, spam detection, and quality scoring. Groups all content normalization and quality rules in a single settings object.

**PersonalizationSettings:**
Configuration for relevance scoring and personalization. Controls keyword weighting, relevance thresholds, boost factors, cache duration, and semantic scoring toggle.

### Dependency Injection Pattern

Processors accept settings via constructor parameters with sensible defaults from global configuration. This allows:

**Production Usage:**
Processors use global settings from environment variables via `get_settings()`. No explicit settings passing required in production code.

**Testing Flexibility:**
Tests can create custom settings objects with specific values for test scenarios. Easy to test edge cases and specific configurations.

**Optional Override:**
Settings parameters default to None and fallback to `get_settings().<group>`. Explicit settings can be passed when needed without changing default behavior.

### Security Configuration
Accessed via `settings.security.*`
- `SECURITY__SECRET_KEY`: Secret key for JWT token signing (required)
- `SECURITY__JWT_EXPIRE_MINUTES`: JWT token expiration in minutes (default: 30)

### Application Configuration
- `APP_NAME`: Application name (default: "Personal Daily Reading Digest")
- `APP_VERSION`: Application version
- `APP_ENV`: Environment (development, staging, production)
- `DEBUG`: Debug mode flag (default: false)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

### Rate Limiting Configuration
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_PER_MINUTE`: Requests per minute per user (default: 60)
- `RATE_LIMIT_BURST`: Burst allowance (default: 10)

## Configuration Loading

### Priority Order
1. Environment variables
2. `.env` file in project root
3. `.env.local` file (gitignored, for local overrides)
4. Default values in code

### Development Configuration
- Use `.env.development` for development-specific settings
- Override with `.env.local` for personal development settings
- Never commit `.env.local` to version control

### Production Configuration
- All configuration via environment variables
- No `.env` files in production
- Use secrets management for sensitive values
- Validate all required settings on startup

## Configuration Validation

### Startup Validation
- All required configuration checked at application startup
- Invalid configuration causes immediate failure with clear error messages
- Type validation via Pydantic ensures correct types
- Range validation for numeric values

### Configuration Testing
- Separate test configuration with test-specific values
- Use environment variable overrides in tests
- Mock external service configurations
- Test configuration loading and validation logic

## Best Practices

1. **Never hardcode secrets**: Always use environment variables
2. **Document all settings**: Include in this file with defaults and descriptions
3. **Validate on startup**: Fail fast with clear error messages
4. **Use type hints**: Pydantic ensures type safety
5. **Provide sensible defaults**: Make development setup easy
6. **Namespace Redis keys**: Prevent conflicts in shared Redis instances
7. **Use descriptive names**: Clear, self-documenting variable names
8. **Group related settings**: Organize by component or feature
