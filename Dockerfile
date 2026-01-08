# logtap Dockerfile
# Multi-stage build for smaller image size

# Build stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export requirements (without dev dependencies)
RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt

# Runtime stage
FROM python:3.10-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash logtap

# Copy requirements and install
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Default environment variables
ENV LOGTAP_HOST=0.0.0.0
ENV LOGTAP_PORT=8000
ENV LOGTAP_LOG_DIRECTORY=/var/log

# Expose port
EXPOSE 8000

# Switch to non-root user
USER logtap

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Run the server
CMD ["python", "-m", "logtap", "serve"]
