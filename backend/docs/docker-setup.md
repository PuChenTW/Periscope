# Docker Development Environment

## Overview

The backend uses Docker Compose to orchestrate multiple services:

- **PostgreSQL** (pgvector/pgvector:pg17): Database with vector extension
- **Redis** (redis:8.2.1): Cache layer
- **Temporal** (temporalio/auto-setup:1.25.2): Workflow orchestration server
- **Temporal UI** (temporalio/ui:2.31.2): Web interface for monitoring workflows
- **App**: FastAPI backend application

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild app after dependency changes
docker-compose up --build app
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| FastAPI App | <http://localhost:8000> | Backend API |
| Temporal UI | <http://localhost:8080> | Workflow monitoring dashboard |
| PostgreSQL | localhost:5432 | Database (periscope/periscope_dev) |
| Redis | localhost:6379 | Cache |
| Temporal gRPC | localhost:7233 | Temporal server |

## Service Dependencies

```text
postgres (healthy)
  ├─> temporal (healthy)
  │     └─> temporal-ui
  │     └─> app
  └─> redis (healthy)
        └─> app
```

## Environment Variables

All services use environment variables defined in `docker-compose.yml`. For local development without Docker, copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

### Key Variables

```bash
# Database
DATABASE__URL=postgresql+asyncpg://periscope:periscope_dev@localhost:5432/periscope

# Redis
REDIS__URL=redis://localhost:6379/0

# Temporal
TEMPORAL__SERVER_URL=localhost:7233
TEMPORAL__NAMESPACE=default
TEMPORAL__TASK_QUEUE=periscope-digest
```

## Temporal Server Setup

### Architecture

Temporal uses PostgreSQL for persistence. The `temporalio/auto-setup` image:

1. Creates Temporal schema in PostgreSQL on first run
2. Starts the Temporal server
3. Registers the `default` namespace

### Health Checks

The Temporal service has a health check with:

- **Initial delay**: 30 seconds (allows schema setup)
- **Interval**: 10 seconds
- **Retries**: 10 attempts
- **Timeout**: 5 seconds per check

The app service waits for Temporal to be healthy before starting.

### Temporal UI

Access the Temporal Web UI at <http://localhost:8080> to:

- View workflow executions
- Inspect activity logs
- Debug workflow failures
- Query workflow state
- Cancel/terminate workflows

### Configuration

Dynamic configuration is stored in `temporal-config/development-sql.yaml`. Modify this file to adjust:

- Workflow retention periods
- Debug mode settings
- Search attribute behavior

Restart Temporal after configuration changes:

```bash
docker-compose restart temporal
```

## Development Workflow

### Initial Setup

```bash
# Start services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# Run migrations (if needed)
docker-compose exec app uv run alembic upgrade head
```

### Working with Services

```bash
# View specific service logs
docker-compose logs -f app
docker-compose logs -f temporal

# Restart a service
docker-compose restart app

# Execute commands in running container
docker-compose exec app uv run pytest
docker-compose exec app uv run python -m app.scripts.seed_data

# Access PostgreSQL
docker-compose exec postgres psql -U periscope -d periscope

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Temporal CLI Commands

Install Temporal CLI (`tctl`) for advanced operations:

```bash
# On macOS
brew install temporal

# List workflows
tctl --address localhost:7233 workflow list

# Describe workflow
tctl --address localhost:7233 workflow describe -w <workflow-id>

# Cancel workflow
tctl --address localhost:7233 workflow cancel -w <workflow-id>
```

## Troubleshooting

### Temporal Server Not Starting

**Symptom**: `temporal` service exits or restarts repeatedly

**Solution**:

1. Check PostgreSQL is healthy: `docker-compose ps postgres`
2. View Temporal logs: `docker-compose logs temporal`
3. Reset Temporal schema:

   ```bash
   docker-compose down -v
   docker-compose up postgres redis
   # Wait 10 seconds
   docker-compose up temporal
   ```

### App Cannot Connect to Temporal

**Symptom**: App logs show connection errors to Temporal

**Solution**:

1. Verify Temporal is healthy: `docker-compose ps temporal`
2. Check environment variables: `docker-compose exec app env | grep TEMPORAL`
3. Test connection from app container:

   ```bash
   docker-compose exec app python -c "
   import asyncio
   from app.temporal.client import get_temporal_client
   asyncio.run(get_temporal_client())
   "
   ```

### Port Conflicts

**Symptom**: Services fail to start with "port already in use"

**Solution**:

1. Check what's using the port:

   ```bash
   lsof -i :8000  # FastAPI
   lsof -i :7233  # Temporal
   lsof -i :8080  # Temporal UI
   ```

2. Stop conflicting processes or change ports in `docker-compose.yml`

### Volume Permission Issues

**Symptom**: PostgreSQL fails to start with permission errors

**Solution**:

```bash
# Reset volumes
docker-compose down -v

# Restart with fresh volumes
docker-compose up -d
```

## Production Considerations

When deploying to production:

1. **Temporal Server**:
   - Use dedicated Temporal cluster (not `auto-setup` image)
   - Configure TLS/mTLS for secure gRPC communication
   - Set up Temporal Cloud or self-hosted cluster
   - Use separate PostgreSQL instance with replication

2. **Database**:
   - Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
   - Enable SSL connections
   - Configure connection pooling

3. **Redis**:
   - Use managed Redis (AWS ElastiCache, Redis Enterprise, etc.)
   - Enable persistence (AOF or RDB)
   - Configure replica for high availability

4. **Environment Variables**:
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Never commit `.env` file to version control
   - Rotate secrets regularly

5. **Monitoring**:
   - Enable Temporal metrics export (Prometheus/Datadog)
   - Set up workflow failure alerts
   - Monitor database and cache performance

## References

- [Temporal Server Configuration](https://docs.temporal.io/references/server-options)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
