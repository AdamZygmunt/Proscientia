from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from ..config import MOCK_DATA_ROOT, DOCS_DIR

router = APIRouter(prefix="/files", tags=["files"])

@router.get("")
def get_single_file(
    name: str = Query(..., description="Nazwa pliku (np. instrukcja_montazu_v2.pdf)"),
    date: str | None = Query(default=None, description="YYYY-MM-DD (dla plików w erp/mes)"),
    stream: str | None = Query(default=None, description="erp | mes | docs"),
):
    """
    Zwraca pojedynczy plik:
      - stream=docs -> szuka w data/docs/{name}
      - stream=erp/mes -> szuka w data/{stream}/{date}/{name}
    """
    if stream not in {"erp", "mes", "docs"}:
        raise HTTPException(status_code=400, detail="Invalid 'stream' (erp|mes|docs)")

    if stream == "docs":
        path = DOCS_DIR / name
    else:
        if not date:
            raise HTTPException(status_code=400, detail="For erp/mes provide 'date'")
        path = MOCK_DATA_ROOT / stream / date / name

    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path.name}")

    # FastAPI/Starlette ustawi Content-Type na podstawie rozszerzenia
    return FileResponse(path)
