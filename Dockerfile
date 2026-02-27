# =============================================================================
# Azure Governance Platform - Production Dockerfile
# Multi-stage build for optimized container size and security
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Build arguments
ARG PYTHON_VERSION=3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Set work directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --system flag installs to system Python (needed for multi-stage)
RUN uv pip install --system -e . \
    && uv pip install --system gunicorn uvicorn

# Clean up
RUN rm -rf /root/.cache

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

LABEL maintainer="Cloud Governance Team" \
      application="Azure Governance Platform" \
      version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    APP_USER=appuser \
    APP_GROUP=appgroup \
    PORT=8000 \
    # App Service specific settings
    WEBSITE_HEALTHCHECK_MAXPINGFAILURES=3 \
    WEBSITES_PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for health checks
    curl \
    # Required for SQL connectivity (if using Azure SQL)
    libodbc1 \
    libodbc2 \
    # Security updates
    ca-certificates \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd --gid 1000 ${APP_GROUP} && \
    useradd --uid 1000 --gid ${APP_GROUP} \
    --shell /bin/bash --create-home ${APP_USER}

# Set work directory
WORKDIR ${APP_HOME}

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} app/ ./app/
COPY --chown=${APP_USER}:${APP_GROUP} scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /home/data /home/logs /tmp && \
    chown -R ${APP_USER}:${APP_GROUP} /home/data /home/logs /tmp && \
    chmod 755 /home/data /home/logs

# Switch to non-root user
USER ${APP_USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run the application
# Using exec form for proper signal handling
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 3: Development image (optional - includes dev dependencies)
# -----------------------------------------------------------------------------
FROM builder as development

LABEL maintainer="Cloud Governance Team" \
      application="Azure Governance Platform" \
      version="1.0.0-dev"

# Install development dependencies
RUN uv pip install --system -e ".[dev]"

WORKDIR /app

# Copy full application
COPY . .

# Create data directory
RUN mkdir -p /app/data && chmod 755 /app/data

# Run in development mode
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
