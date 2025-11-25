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


@router.get("/docs-list")
def list_docs() -> dict:
    """
    Zwraca listę dokumentów dostępnych w katalogu `data/docs/`.

    Jeśli są podkatalogi (np. budownictwo/, finance/, ventilator_pb560/),
    zwracamy ścieżkę względną względem DOCS_DIR:
      - "ventilator_pb560/spec_pb560_requirements.pdf"
    """
    if not DOCS_DIR.exists():
        return {"files": []}

    files: list[dict] = []
    for p in DOCS_DIR.rglob("*"):
        if p.is_file():
            rel_path = p.relative_to(DOCS_DIR).as_posix()
            files.append(
                {
                    "name": rel_path,
                    "size": p.stat().st_size,
                }
            )

    files_sorted = sorted(files, key=lambda x: x["name"])
    return {"files": files_sorted}