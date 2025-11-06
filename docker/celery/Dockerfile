# Dev image for Celery (worker/beat) reusing Django backend code
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

COPY backend/ /app/

COPY docker/celery/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Brak EXPOSE — Celery nie wystawia portów
CMD ["/entrypoint.sh"]
