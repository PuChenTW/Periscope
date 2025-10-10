# Database Design Guidelines

## Schema Design Rules

1. **Use ULIDs for primary keys** - Better for distributed systems, sortable by creation time
2. **Include audit fields** - created_at, updated_at using mixins
3. **Soft delete pattern** - Use deleted_at instead of hard deletes (future enhancement)
4. **Proper indexing** - Index foreign keys and frequently queried fields
5. **Constraints** - Use database constraints for data integrity

## Base Model Patterns

### ULID Mixin
Provides string-based primary keys that are sortable and distributed-system friendly.

**Benefits:**
- Globally unique without coordination
- Lexicographically sortable by creation time
- URL-safe string representation
- Better for distributed systems than UUIDs

### Timestamp Mixin
Automatic created_at and updated_at fields with database-level defaults.

**Features:**
- Automatically set on record creation
- Automatically updated on record modification
- Database-level default values
- Timezone-aware timestamps

### SQLModel Integration
Combine with SQLModel for type-safe ORM with automatic API schema generation.

**Advantages:**
- Single source of truth for models and API schemas
- Type safety with Pydantic validation
- Automatic OpenAPI documentation
- Seamless FastAPI integration

## Key Entity Relationships

### User
Central entity with email-based authentication, timezone awareness, and verification status.

**Key Fields:**
- `id` (ULID): Primary key
- `email`: Unique, indexed
- `hashed_password`: bcrypt hash
- `is_verified`: Email verification status
- `timezone`: User's timezone for delivery scheduling
- `created_at`, `updated_at`: Audit timestamps

### DigestConfiguration
Per-user settings for delivery time, summary style, and source management.

**Key Fields:**
- `user_id` (FK): One-to-one with User
- `delivery_hour`: Hour of day (0-23)
- `delivery_minute`: Minute of hour (0-59)
- `summary_style`: Enum (brief, detailed, bullet_points)
- `is_active`: Enable/disable digest delivery

**Relationships:**
- One-to-one with User
- One-to-many with ContentSource

### ContentSource
User-configured RSS feeds and blog URLs with validation status.

**Key Fields:**
- `config_id` (FK): References DigestConfiguration
- `source_type`: Enum (rss, blog)
- `url`: Source URL
- `is_active`: Enable/disable source
- `last_validated`: Last successful fetch timestamp
- `validation_status`: Enum (valid, invalid, pending)

**Relationships:**
- Many-to-one with DigestConfiguration

### InterestProfile
Keyword-based personalization with relevance scoring.

**Key Fields:**
- `config_id` (FK): One-to-one with DigestConfiguration
- `keywords`: JSON array of normalized interest keywords (max 50)
- `relevance_threshold`: Minimum score for content inclusion (0-100, default 40)
- `boost_factor`: Multiplier applied to final relevance score (range 0.5-2.0, default 1.0)

**Relationships:**
- One-to-one with DigestConfiguration

## Indexing Strategy

**Primary Indexes:**
- All foreign keys
- `user.email` (unique)
- `content_source.url`
- `content_source.is_active`

**Composite Indexes:**
- `(user_id, is_active)` for active user queries
- `(config_id, is_active)` for active source queries

## Data Integrity Constraints

- Email uniqueness at database level
- Foreign key constraints with CASCADE delete (where appropriate)
- Check constraints for valid hour/minute ranges
- Not-null constraints on critical fields
- Enum validation at database level
