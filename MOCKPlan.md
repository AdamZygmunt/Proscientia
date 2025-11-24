# Wolumeny i wersjonowanie danych w mock-API (FastAPI)

***Cel:*** realistyczna symulacja ERP/MES, wiele wersji plików (*PDF/DOCX/XLSX/JSON*), śledzenie zmian w czasie.

---

### Proponowana struktura plików

```bash
mock/
├─ app/                 # kod FastAPI
├─ data/                # BIND MOUNT do kontenera: /data
│  ├─ erp/
│  │  ├─ 2025-11-06/
│  │  │  ├─ work_orders.json
│  │  │  ├─ bom.xlsx
│  │  │  └─ instrukcja_montażu_v1.pdf
│  │  └─ 2025-11-12/
│  │     ├─ work_orders.json
│  │     ├─ bom.xlsx                    # np. zmieniony BOM
│  │     └─ instrukcja_montażu_v2.pdf   # nowa wersja PDF
│  ├─ mes/
│  │  ├─ 2025-11-06/
│  │  │  ├─ quality_report.json
│  │  │  └─ downtime_log.json
│  │  └─ 2025-11-12/
│  │     ├─ quality_report.json
│  │     └─ downtime_log.json
│  └─ docs/             # surowe dokumenty (PDF/DOCX/XLSX), które mock linkuje
│     ├─ instrukcja_montażu_v1.pdf
│     └─ instrukcja_montażu_v2.pdf
└─ manifest.json        # indeks wersji i checksumy (patrz niżej)
```

---

### Wersjonowanie

1. Każda *„releasowa”* migawka ERP/MES ląduje w folderze daty ***YYYY-MM-DD*** (ew. *YYYY-MM-DDThhmmss* przy wielu publikacjach dziennie).

2. ***manifest.json*** w mock/:
 - mapuje latest dla każdego strumienia danych (erp/mes) na konkretną datę,
 - trzyma checksumy (SHA256) i metadane (rozmiar, updated_at) dla plików i rekordów, żeby backend mógł porównywać i szybko wykrywać zmiany.
 - przykład:
 ```json
    {  
        "erp": {"latest": "2025-11-12"},
        "mes": {"latest": "2025-11-12"},
        "checksums": {
            "docs/instrukcja_montażu_v2.pdf": "sha256:…"
        }
    }
 ```

3. ***API - FastAPI:***
 - **GET /erp?version=YYYY-MM-DD** (brak = latest z manifest.json),
 - **GET /mes?version=YYYY-MM-DD**,
 - **GET /docs/{filename}** – serwuje pliki z /data/docs.
 - **Nagłówki: ETag (checksum), Last-Modified** → backend może robić conditional GET (If-None-Match / If-Modified-Since) i reindeksować tylko zmienione pliki.

4. ***Wolumen:*** bind-mount *./mock/data → /data* tylko do kontenera mock-API. Backend nie czyta z dysku mocka — idzie przez HTTP (żeby było *„jak prawdziwa integracja”*).