# Multi-stage build for AI Agent Platform Orchestrator
FROM python:3.11-slim as builder

# Set build arguments
ARG AWS_REGION=us-east-1
ARG ENVIRONMENT=prod

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AWS_REGION=${AWS_REGION} \
    ENVIRONMENT=${ENVIRONMENT}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /build

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set runtime arguments
ARG AWS_REGION=us-east-1
ARG ENVIRONMENT=prod
ARG CONTAINER_PORT=8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AWS_REGION=${AWS_REGION} \
    ENVIRONMENT=${ENVIRONMENT} \
    CONTAINER_PORT=${CONTAINER_PORT}

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Create app directories
RUN mkdir -p /app /var/log /tmp && \
    chown -R appuser:appuser /app /var/log /tmp

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser src/ /app/

# Copy entrypoint script
COPY --chown=appuser:appuser docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${CONTAINER_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${CONTAINER_PORT}/health || exit 1

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "platform.api.main:app", "--host", "0.0.0.0", "--port", "${CONTAINER_PORT}"]
