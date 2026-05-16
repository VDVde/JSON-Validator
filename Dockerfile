# Multi-stage Dockerfile for VDV463 Validator

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY web/frontend/package*.json ./
RUN npm install
COPY web/frontend/ ./
RUN npm run build

# Stage 2: Runtime Stage
FROM python:3.12-alpine

# Security: Install security updates
RUN apk update && apk upgrade --no-cache \
    && rm -rf /var/cache/apk/*

# Security: Create non-root user, app directory, and set permissions
RUN addgroup -g 1000 validator \
    && adduser -D -u 1000 -G validator validator \
    && mkdir -p /home/validator/app \
    && chown -R validator:validator /home/validator

# Security: Set restrictive file permissions
WORKDIR /home/validator/app

# Copy python dependencies first (better layer caching)
COPY --chown=validator:validator pyproject.toml README.md ./
COPY --chown=validator:validator requirements-docker.txt requirements.txt
COPY --chown=validator:validator web/backend/requirements.txt ./web/backend/

# Switch to non-root user for pip install
USER validator

# Install dependencies (user level, no cache)
ENV PATH="/home/validator/.local/bin:$PATH"
RUN pip install --no-cache-dir --user .[docker,web]

# Copy source code with restricted permissions
COPY --chown=validator:validator src ./src
COPY --chown=validator:validator web/backend ./web/backend

# Create schemas and data directories
RUN mkdir -p ./schemas ./web/backend/data && chown validator:validator ./schemas ./web/backend/data

# Copy built frontend from Stage 1
COPY --from=frontend-builder --chown=validator:validator /app/frontend/dist ./web/frontend/dist

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/home/validator/app/src:/home/validator/app/web/backend"
ENV PYTHONDONTWRITEBYTECODE=1

# Data volume for persistence
VOLUME ["/home/validator/app/web/backend/data"]

# SECURITY: Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Run application with production settings
CMD ["uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
