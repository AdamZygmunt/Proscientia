from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MockErpMesClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.base_url = base_url or getattr(settings, "MOCK_API_BASE", "").rstrip("/")
        if not self.base_url:
            raise ValueError("MOCK_API_BASE must be configured in settings/.env")
        self.timeout = timeout

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}{path}"
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp

    # --- MANIFEST ---

    def get_manifest(self, use_cache: bool = True) -> Dict[str, Any]:
        cache_key = "mock:manifest"

        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        resp = self._get("/manifest")
        data = resp.json()

        cache.set(cache_key, data, timeout=900)  # 15 minut
        return data

    # --- ERP / MES listing ---

    def get_stream_listing(
        self, stream: str, date: Optional[str] = None, use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        stream: "erp" lub "mes"
        zwraca dict np. { "date": "2025-12-15", "files": [ { name, size }, ... ] }
        """
        if stream not in ("erp", "mes"):
            raise ValueError(f"Invalid stream: {stream}")

        cache_key = f"mock:{stream}:listing:{date or 'latest'}"
        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        params = {}
        if date:
            params["date"] = date

        path = f"/{stream}"
        resp = self._get(path, params=params)
        data = resp.json()

        cache.set(cache_key, data, timeout=300)
        return data

    # --- Files (JSON / PDF / inne) ---

    def get_file_bytes(
        self,
        stream: str,
        name: str,
        date: Optional[str] = None,
    ) -> bytes:
        """
        Pobiera bajty pliku z endpointu /files.
        STREAM:
          - "docs" -> pliki z data/docs/
          - "erp" / "mes" -> pliki dla danego snapshotu (wymaga date)
        """
        params: Dict[str, Any] = {"stream": stream, "name": name}
        if stream in ("erp", "mes"):
            if not date:
                raise ValueError("date is required for erp/mes file")
            params["date"] = date

        resp = self._get("/files", params=params)
        return resp.content
