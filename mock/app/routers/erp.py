from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import List
from ..config import MOCK_DATA_ROOT
from ..utils.manifest import read_manifest, latest_for

router = APIRouter(prefix="/erp", tags=["erp"])

@router.get("")
def get_erp_listing(date: str | None = Query(default=None, description="YYYY-MM-DD (brak = latest)")):
    manifest = read_manifest(MOCK_DATA_ROOT / "manifest.json")
    target_date = date or latest_for("erp", manifest)
    if not target_date:
        return {"date": None, "files": []}

    folder = MOCK_DATA_ROOT / "erp" / target_date
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"ERP snapshot for {target_date} not found")

    files = []
    for p in folder.iterdir():
        if p.is_file():
            files.append({"name": p.name, "size": p.stat().st_size})
    return {"date": target_date, "files": sorted(files, key=lambda x: x["name"])}
