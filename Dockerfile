# Streamable-HTTP deployment image. Works on Railway, Fly.io, Render, Cloud Run,
# or anywhere else that sets $PORT; the resulting /mcp endpoint is what you
# register with Smithery's URL publishing flow.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_TRANSPORT=http \
    PORT=8081

WORKDIR /app

# Install dependencies first so edits to src/ don't invalidate this layer.
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Run unprivileged.
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8081
CMD ["google-rss-mcp"]
