#!/usr/bin/env bash
set -e

# ROLE=worker|beat (domyślnie worker)
ROLE="${ROLE:-worker}"

# Ustaw domyślny moduł settings, jeśli nie podano
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.dev}"

# Informacyjnie
echo "[celery] ROLE=${ROLE}"
echo "[celery] DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
echo "[celery] REDIS_URL=${REDIS_URL:-not-set}"
echo "[celery] DATABASE: ${DB_NAME:-} @ ${DB_HOST:-}:${DB_PORT:-}"

cd /app

if [ "$ROLE" = "beat" ]; then
  echo "[celery] Starting Celery Beat..."
  exec celery -A config.celery_app beat -l INFO
else
  echo "[celery] Starting Celery Worker..."
  exec celery -A config.celery_app worker -l INFO --pool=threads
fi
