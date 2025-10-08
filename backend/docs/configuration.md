# Configuration Management

## Environment-based Configuration

Use Pydantic BaseSettings for type-safe configuration management. All configuration is loaded from environment variables with support for .env files.

## Configuration Categories

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_POOL_SIZE`: Connection pool size (default: 20)
- `DATABASE_MAX_OVERFLOW`: Maximum overflow connections (default: 10)
- `DATABASE_POOL_TIMEOUT`: Connection timeout in seconds (default: 30)
- `DATABASE_POOL_RECYCLE`: Connection recycle time in seconds (default: 3600)

### Caching Configuration
- `REDIS_URL`: Redis connection URL
- `REDIS_PASSWORD`: Redis authentication password (optional)
- `REDIS_MAX_CONNECTIONS`: Maximum connection pool size (default: 50)
- `REDIS_DEFAULT_TTL`: Default cache TTL in seconds (default: 3600)
- `REDIS_KEY_PREFIX`: Key prefix for namespacing (default: "periscope:")

### Temporal Configuration
- `TEMPORAL_HOST`: Temporal server host (default: "localhost")
- `TEMPORAL_PORT`: Temporal server port (default: 7233)
- `TEMPORAL_NAMESPACE`: Temporal namespace (default: "default")
- `TEMPORAL_TASK_QUEUE`: Task queue name (default: "digest-tasks")

### Email Provider Configuration
- `EMAIL_PROVIDER`: Provider name (sendgrid, ses, smtp)
- `EMAIL_API_KEY`: Provider API key
- `EMAIL_FROM_ADDRESS`: Sender email address
- `EMAIL_FROM_NAME`: Sender display name
- `SMTP_HOST`: SMTP server host (for SMTP provider)
- `SMTP_PORT`: SMTP server port (default: 587)
- `SMTP_USERNAME`: SMTP authentication username
- `SMTP_PASSWORD`: SMTP authentication password

### AI Provider Settings
- `AI_PROVIDER`: Provider selection (gemini, openai, anthropic, etc.)
- `GEMINI_API_KEY`: Google Gemini API key
- `GEMINI_MODEL`: Model name (default: gemini-2.5-flash-lite)
- `OPENAI_API_KEY`: OpenAI API key (for future use)
- `OPENAI_MODEL`: OpenAI model name (for future use)

### Similarity Detection Configuration
- `SIMILARITY_THRESHOLD`: Minimum confidence score for similarity (default: 0.7, range: 0.0-1.0)
- `SIMILARITY_CACHE_TTL_MINUTES`: Cache duration for similarity results (default: 1440 = 24 hours)
- `SIMILARITY_MAX_COMPARISONS`: Maximum article pairs to compare (default: 100)

### Topic Extraction Configuration
- `TOPIC_EXTRACTION_MAX_TOPICS`: Maximum topics per article (default: 5, range: 1-10)
- `TOPIC_EXTRACTION_CONTENT_LENGTH`: Max content chars for extraction (default: 1000)

### Content Processing Configuration
- `HTTP_CLIENT_TIMEOUT`: Default HTTP request timeout in seconds (default: 30)
- `HTTP_CLIENT_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `HTTP_CLIENT_RETRY_DELAY`: Delay between retries in seconds (default: 2)
- `RSS_FETCH_TIMEOUT`: Specific timeout for RSS fetching (default: 20)
- `CONTENT_FETCH_BATCH_SIZE`: Number of sources to fetch in parallel (default: 10)

### Security Configuration
- `JWT_SECRET_KEY`: Secret key for JWT token signing (required)
- `JWT_ALGORITHM`: JWT signing algorithm (default: "HS256")
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration (default: 30)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: 7)
- `PASSWORD_MIN_LENGTH`: Minimum password length (default: 8)
- `PASSWORD_REQUIRE_UPPERCASE`: Require uppercase letters (default: true)
- `PASSWORD_REQUIRE_NUMBERS`: Require numbers (default: true)
- `PASSWORD_REQUIRE_SPECIAL`: Require special characters (default: true)

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
