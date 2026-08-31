# ==========================================
# Step 1: Builder (wheel compilation)
# ==========================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Build tools required to compile potential C extensions
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build isolated wheels into /app/wheels
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# ==========================================
# Step 2: Final production image
# ==========================================
FROM python:3.11-slim-bookworm AS final

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# PostgreSQL client runtime library only (no compilers)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Retrieve and install prebuilt wheels from the builder stage
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .

RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    pip uninstall -y setuptools wheel pip && \
    rm -rf /wheels

# Copy application source code
COPY . .

# Security: non-root user
RUN mkdir -p /app/staticfiles /app/mediafiles && \
    useradd -u 8888 django-user && \
    chown -R django-user:django-user /app

USER django-user

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]