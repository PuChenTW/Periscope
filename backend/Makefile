REVISION ?= head
STEP     ?= 1
MESSAGE  ?= ""

.PHONY: help install start stop test lint format clean dev

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with UV
	uv sync

start:  ## Start all services with Docker Compose
	docker compose up -d
	@echo "Services starting... Access API at http://localhost:8000"

stop:  ## Stop all services
	docker compose down

restart:  ## Restart all services
	docker compose restart

test:  ## Run pytest test suite
	uv run pytest tests/ -v

lint:  ## Run linting checks
	uv run ruff check app/ tests/
	uv run mypy app/

format:  ## Format code with ruff
	uv run ruff format app/ tests/

ruff-file: ## Format and fix a specific file with ruff (usage: make ruff-file FILE=path/to/file.py)
	uv run ruff format $(FILE)
	uv run ruff check --fix $(FILE)

clean:  ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

dev:  ## Start development environment
	docker compose up -d postgres
	uv run uvicorn app.main:create_app --host 0.0.0.0 --port 8000 --reload

build:  ## Build Docker images
	docker compose build

health:  ## Check service health
	curl -f http://localhost:8000/health || echo "API not responding"

logs:  ## Show service logs
	docker compose logs -f

db-shell:  ## Connect to database shell
	docker compose exec postgres psql -U periscope -d periscope

mg:			# run database migration to the latest version
	uv run alembic upgrade $(REVISION)

mg-heads:	# list all heads
	uv run alembic heads

mg-down:	# run database migration to the latest version
	uv run alembic downgrade -$(STEP)

mg-rev:		# create a new migration revision
	uv run alembic revision --autogenerate -m "$(MESSAGE)"

mg-merge:	# merge all heads roughly, use with caution (should check the migration script)
	@HEADS=$$(uv run alembic heads | cut -d ' ' -f1 | tr '\n' ' '); \
	if [ -n "$$HEADS" ]; then \
		echo "Merging Alembic heads: $$HEADS"; \
		uv run alembic merge $$HEADS -m "$(MESSAGE)"; \
	else \
		echo "No multiple heads found."; \
	fi