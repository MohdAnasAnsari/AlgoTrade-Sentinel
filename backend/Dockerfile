FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/backend:/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip && pip install -r backend/requirements.txt

COPY backend /app/backend
COPY ml /app/ml
COPY mlops /app/mlops
COPY config /app/config
COPY scripts /app/scripts

RUN chmod +x /app/scripts/*.sh \
    && mkdir -p /app/ml/artifacts/models \
                /app/ml/artifacts/datasets \
                /app/ml/artifacts/monitoring \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

WORKDIR /app/backend
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
