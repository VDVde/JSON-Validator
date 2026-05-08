# Optimized Dockerfile for VDV463 Validator
# This version expects the frontend to be pre-built in web/frontend/dist

# Runtime Stage
FROM python:3.12-alpine

# Security: Install security updates
RUN apk update && apk upgrade --no-cache \
    && rm -rf /var/cache/apk/*

# Security: Create non-root user with specific UID/GID
RUN addgroup -g 1000 validator \
    && adduser -D -u 1000 -G validator validator

# Security: Set restrictive file permissions
WORKDIR /home/validator/app

# Copy python dependencies first (better layer caching)
COPY --chown=validator:validator requirements-docker.txt requirements.txt
COPY --chown=validator:validator web/backend/requirements.txt ./web/backend/

# Switch to non-root user for pip install
USER validator

# Install dependencies (user level, no cache)
ENV PATH="/home/validator/.local/bin:$PATH"
RUN pip install --no-cache-dir --user -r requirements.txt \
    && pip install --no-cache-dir --user -r web/backend/requirements.txt

# Copy source code with restricted permissions
COPY --chown=validator:validator src ./src
COPY --chown=validator:validator schemas ./schemas
COPY --chown=validator:validator web/backend ./web/backend

# Create data directory for SQLite database (writable by validator user)
RUN mkdir -p ./web/backend/data

# Copy pre-built frontend
# IMPORTANT: Run 'npm run build' in web/frontend before building this image!
COPY --chown=validator:validator web/frontend/dist ./web/frontend/dist

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
