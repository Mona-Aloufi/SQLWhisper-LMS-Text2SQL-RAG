# SQLWhisper Text2SQL - Dockerfile
# Multi-stage build for optimized image size

# ============================================================
# Stage 1: Base image with Python and system dependencies
# ============================================================
FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================
# Stage 2: Dependencies installation
# ============================================================
FROM base AS dependencies

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 3: Final application image
# ============================================================
FROM dependencies AS app

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data streamlit_app streamlit_app/streamlit_app

# Set permissions
RUN chmod -R 755 /app

# Expose ports
# 8000: FastAPI backend
# 8501: Streamlit frontend
EXPOSE 8000 8501

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ============================================================
# Entry point
# ============================================================
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

CMD ["docker-entrypoint.sh"]
