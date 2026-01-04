FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Install package in editable mode
RUN pip install -e .

# Create volume for state persistence
VOLUME ["/app/data"]

# Environment variables will be provided via .env or docker-compose
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 \
  CMD shopping-sync --check || exit 1

CMD ["shopping-sync"]
