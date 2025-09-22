FROM python:3.13-slim

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]