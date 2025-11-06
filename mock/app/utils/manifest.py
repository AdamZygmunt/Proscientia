from __future__ import annotations
from pathlib import Path
import json
from typing import Any

def read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def latest_for(stream: str, manifest: dict[str, Any]) -> str | None:
    # manifest struktura np. {"erp":{"latest":"2025-11-12"}, "mes":{"latest":"2025-11-12"}}
    node = manifest.get(stream)
    if isinstance(node, dict):
        return node.get("latest")
    return None
