#!/usr/bin/env bash
set -e

: "${MOCK_DATA_ROOT:=/data}"
: "${MOCK_MANIFEST_PATH:=${MOCK_DATA_ROOT}/manifest.json}"

# Przygotuj strukturę danych (jeśli wolumen jest pusty)
mkdir -p "${MOCK_DATA_ROOT}/erp" "${MOCK_DATA_ROOT}/mes" "${MOCK_DATA_ROOT}/docs"

# Minimalny manifest, jeśli nie istnieje
if [ ! -f "${MOCK_MANIFEST_PATH}" ]; then
  echo '{
  "erp": { "latest": null },
  "mes": { "latest": null }
}' > "${MOCK_MANIFEST_PATH}"
fi

# Informacyjnie wypisz ścieżki
echo "[mock] Using MOCK_DATA_ROOT=${MOCK_DATA_ROOT}"
echo "[mock] Using MOCK_MANIFEST_PATH=${MOCK_MANIFEST_PATH}"

# Start FastAPI + autoreload (dev)
exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# fox