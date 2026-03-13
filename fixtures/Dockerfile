# Dockerfile — Multi-stage build for the inventory API service
# Base image: Python 3.12-slim for minimal attack surface
# Deployed to ECS Fargate behind an ALB

# ── Stage 1: Builder ─────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY . .

# ── Stage 2: Runtime ─────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY --from=builder /build/src ./src
COPY --from=builder /build/alembic.ini .
COPY --from=builder /build/migrations ./migrations

# ── Secrets passed as ENV (should use runtime secrets) ───
# These are baked into the image layer — visible via `docker history`
ENV DATABASE_URL="postgresql://inventory_svc:Pr0d_S3rv1c3_P4ss!@db.internal.corp.net:5432/inventory_prod"
ENV REDIS_URL="redis://:r3d1s_s3cr3t_2025@cache.internal.corp.net:6379/0"
ENV AWS_ACCESS_KEY_ID="AKIAWR3DPKFJ9T2QX5NB"
ENV AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYz0+Q39vAs8"
ENV STRIPE_SECRET_KEY="sk_live_51NvGk2CjsR8tWvY3bLm4dOqA7fZxN9pKhViEw5u"
ENV JWT_SECRET="production_jwt_signing_secret_do_not_leak"

# Non-secret config (these are fine as ENV)
ENV APP_ENV="production"
ENV APP_PORT="8080"
ENV WORKERS="4"
ENV LOG_LEVEL="info"

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE ${APP_PORT}

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
