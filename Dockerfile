# 1. Base image
FROM python:3.11-slim-bookworm

WORKDIR /app

# 2. Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. System dependencies for MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY . .

# 6. Security: Non-root user (DevSecOps)
RUN mkdir -p /app/staticfiles /app/mediafiles && \
    useradd -u 8888 django-user && \
    chown -R django-user:django-user /app

USER django-user

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]