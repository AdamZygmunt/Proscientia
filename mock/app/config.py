from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Katalog z danymi; można nadpisać zmiennymi środowiskowymi
MOCK_DATA_ROOT = Path(os.getenv("MOCK_DATA_ROOT", BASE_DIR / "data")).resolve()
MOCK_MANIFEST_PATH = Path(os.getenv("MOCK_MANIFEST_PATH", MOCK_DATA_ROOT / "manifest.json")).resolve()
DOCS_DIR = MOCK_DATA_ROOT / "docs"

# Proste parse date (YYYY-MM-DD), bez twardej walidacji na razie
def normalize_date(date: str | None) -> str | None:
    return date.strip() if date else None
