from fastapi import APIRouter
from ..config import MOCK_MANIFEST_PATH
from ..utils.manifest import read_manifest

router = APIRouter(tags=["manifest"])

@router.get("/manifest")
def get_manifest():
    """
    Zwraca zawartość manifestu wersji ERP/MES.

    Przykład:
    {
      "erp": {
        "latest": "2026-03-30",
        "versions": ["2025-12-15", ...]
      },
      "mes": {
        "latest": "2026-03-30",
        "versions": ["2025-12-15", ...]
      }
    }
    """
    manifest = read_manifest(MOCK_MANIFEST_PATH)
    return manifest
