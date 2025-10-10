# Performance and Monitoring

## 1. Caching Strategy

### Redis Usage

Redis serves as the primary caching layer for frequently accessed data and computationally expensive operations.

**Cache Categories:**

#### User Configuration Cache
- **Key Pattern**: `config:user:{user_id}`
- **TTL**: 1 hour
- **Invalidation**: On configuration updates
- **Purpose**: Avoid repeated database queries for user settings

#### Processed Content Cache
- **Key Pattern**: `content:article:{article_hash}`
- **TTL**: 24 hours
- **Purpose**: Store processed article content to avoid reprocessing

#### Similarity Detection Cache
- **Key Pattern**: `similarity:{article1_hash}:{article2_hash}`
- **TTL**: 24 hours (configurable via SIMILARITY_CACHE_TTL_MINUTES)
- **Purpose**: Avoid redundant AI calls for article comparison

#### API Response Cache
- **Key Pattern**: `api:response:{endpoint}:{params_hash}`
- **TTL**: 5-15 minutes (depending on endpoint)
- **Purpose**: Cache frequently accessed API responses

### Cache Keys

Structured naming convention for consistent access patterns and easy debugging.

**Key Structure:**
```
{namespace}:{entity_type}:{identifier}[:{sub_identifier}]
```

**Examples:**
- `periscope:config:user:01ARZ3NDEKTSV4RRFFQ69G5FAV`
- `periscope:similarity:abc123:def456`
- `periscope:content:article:xyz789`

### Cache Invalidation

Event-based invalidation triggered by configuration changes and data updates.

**Invalidation Triggers:**
- User configuration updates → Clear user config cache
- Source addition/removal → Clear related content cache
- Interest profile changes → Clear relevance scoring cache
- Manual cache clear via admin endpoint

## 2. Monitoring Points

### API Metrics

Track request count, response time, and error rates across endpoints.

**Key Metrics:**
- **Request Count**: Total requests per endpoint
- **Response Time**: P50, P95, P99 latency
- **Error Rate**: 4xx and 5xx response percentages
- **Request Rate**: Requests per second
- **Active Connections**: Current WebSocket/HTTP connections

**Implementation:**
- Middleware-based metric collection
- Prometheus metrics export
- Grafana dashboards

### Workflow Metrics

Track execution time, failure rates, and retry counts for Temporal workflows.

**Key Metrics:**
- **Workflow Duration**: Time to complete digest generation
- **Activity Duration**: Individual activity execution times
- **Failure Rate**: Percentage of failed workflows
- **Retry Count**: Number of activity retries
- **Queue Depth**: Pending workflows in task queue

**Monitoring:**
- Temporal Web UI for workflow visualization
- Temporal metrics exported to Prometheus
- Alerts on workflow failures

### Database Metrics

Monitor connection pool utilization and query performance.

**Key Metrics:**
- **Pool Utilization**: Active vs available connections
- **Query Duration**: Slow query detection (>100ms)
- **Transaction Duration**: Long-running transaction detection
- **Connection Errors**: Failed connection attempts
- **Lock Contention**: Database lock wait times

**Tools:**
- PostgreSQL pg_stat_statements
- Connection pool monitoring
- Slow query logs

### External Service Metrics

Track API call success rates and response times for external dependencies.

**Key Metrics:**
- **RSS Feed Fetch Success Rate**: Percentage of successful fetches
- **AI API Response Time**: Latency for AI operations
- **AI API Error Rate**: Failed AI requests
- **Email Delivery Rate**: Successful email sends
- **External Service Availability**: Uptime monitoring

**Alerting:**
- Alert on low success rates
- Alert on high response times
- Alert on consecutive failures

## 3. Logging Standards

Use structured logging with Loguru for correlation IDs and contextual information.

### Log Levels

**DEBUG**: Detailed diagnostic information
- Function entry/exit with parameters
- Variable state changes
- Cache hits/misses

**INFO**: General informational messages
- Request received/completed
- Workflow started/completed
- Configuration loaded

**WARNING**: Warning messages for unusual situations
- Retrying failed operation
- Degraded functionality
- Near resource limits

**ERROR**: Error messages for failures
- Failed external API calls
- Database errors
- Validation failures

**CRITICAL**: Critical failures requiring immediate attention
- Database connection failures
- Configuration errors
- Service unavailability

### Console and File Handlers

Configure separate handlers for console output (INFO level) and file logging (DEBUG level).

**Console Handler:**
- Level: INFO
- Format: Simple, human-readable
- Colors: Enabled for development

**File Handler:**
- Level: DEBUG
- Format: Structured JSON for parsing
- Rotation: Daily, keep 30 days
- Size limit: 100MB per file

### Log Rotation and Retention

Automatic rotation and retention policies to manage disk space.

**Rotation Policies:**
- **Size-based**: Rotate at 100MB
- **Time-based**: Rotate daily at midnight
- **Retention**: Keep 30 days of logs
- **Compression**: Gzip rotated logs

### Context and Correlation

Include user IDs and operation context for request tracing.

**Contextual Fields:**
- `request_id`: Unique request identifier
- `user_id`: User performing the operation
- `workflow_id`: Temporal workflow identifier
- `correlation_id`: Cross-service request tracking
- `duration_ms`: Operation duration

## 4. Security Considerations

### Authentication & Authorization

**JWT Tokens:**
- Proper expiration times
- Secure signing with strong secret keys
- Token refresh mechanism
- Blacklist for revoked tokens

**Email Verification:**
- Required before digest delivery
- Unique verification tokens
- Token expiration
- Resend verification capability

**Rate Limiting:**
- Per-user rate limits
- Burst allowance for legitimate traffic
- IP-based rate limiting for unauthenticated requests
- Progressive backoff on violations

**Input Validation:**
- Pydantic schema validation on all endpoints
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding
- Path traversal prevention

### Data Protection

**Password Security:**
- Hash sensitive data using bcrypt
- Sufficient bcrypt rounds
- Password complexity requirements
- Prevent password reuse

**Configuration Data:**
- Encrypt sensitive configuration if needed
- Environment variable security
- Secrets rotation policy

**API Keys:**
- Secure external API keys in environment
- Never log API keys
- Rotate keys periodically
- Separate keys per environment

**Communication Security:**
- HTTPS-only communications
- Modern TLS versions
- Certificate validation
- HSTS headers

### Content Security

**URL Validation:**
- Validate all external URLs before fetching
- Whitelist allowed schemes (http, https)
- Block internal network URLs (SSRF prevention)
- Timeout on URL accessibility checks

**Content Sanitization:**
- Sanitize scraped content
- Remove scripts and dangerous HTML
- Validate content types
- Size limits on fetched content

**Rate Limiting for External Requests:**
- Implement rate limiting for external requests
- Respect robots.txt
- User-agent identification
- Backoff on 429 responses

**Malicious Content Handling:**
- Handle malicious content gracefully
- Virus scanning for user uploads (future)
- Content length limits
- Regex DoS prevention

### Security Headers

**HTTP Headers:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy`: Appropriate CSP

### Audit Logging

**Security Events:**
- Failed login attempts
- Password changes
- Permission changes
- API key access
- Suspicious activities

**Audit Trail:**
- Immutable logs
- Tamper detection
- Compliance with retention policies
- Regular audit reviews

## Performance Optimization

### Database Optimization
- Use connection pooling efficiently
- Index frequently queried fields
- Analyze slow queries regularly
- Use prepared statements
- Implement query result caching

### API Optimization
- Implement response compression
- Use pagination for large result sets
- Batch database queries where possible
- Async processing for long operations
- CDN for static assets

### Content Processing Optimization
- Parallel content fetching
- Batch AI operations
- Cache AI results aggressively
- Stream processing for large content
- Throttle external API calls
