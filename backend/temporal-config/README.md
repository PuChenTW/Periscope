# Temporal Configuration

This directory contains dynamic configuration for the Temporal server running in Docker.

## Files

- `development-sql.yaml`: Development configuration with extended retention periods and debug mode

## Configuration Options

The Temporal server uses these settings in development:

- **Workflow Execution Retention**: 7 days (default is 3 days)
- **Debug Mode**: Enabled for verbose logging
- **Search Attributes Cache**: Force refresh on read for consistency

## Modifying Configuration

To add or modify Temporal runtime configuration:

1. Edit `development-sql.yaml`
2. Restart the `temporal` service: `docker-compose restart temporal`
3. Check logs: `docker-compose logs temporal`

## References

- [Temporal Dynamic Configuration](https://docs.temporal.io/references/dynamic-configuration)
- [Temporal Server Configuration](https://docs.temporal.io/references/server-options)

## Production Notes

For production deployments:

- Use separate configuration files per environment
- Reduce retention period to save storage
- Disable debug mode
- Configure TLS/mTLS for secure communication
- Use production-grade PostgreSQL with replication
