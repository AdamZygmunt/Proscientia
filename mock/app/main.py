from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import DOCS_DIR
from .routers import erp as erp_router
from .routers import mes as mes_router
from .routers import files as files_router

app = FastAPI(title="Mock ERP/MES API", version="0.1.0")

# w razie potrzeb można zawęzić - do projektu pokazowego może być '*'
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

# Mount dokumentów statycznych (np. bezpośredni dostęp: /docs/<nazwa_pliku>)
if DOCS_DIR.exists():
    app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")

# Routers
app.include_router(erp_router.router)
app.include_router(mes_router.router)
app.include_router(files_router.router)