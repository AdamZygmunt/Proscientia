# Aplikacja `erp_mes` – integracja mock ERP/MES z backendem

## 1. Cel i rola modułu

Aplikacja `erp_mes` odpowiada za integrację backendu Django z mockowym API ERP/MES (serwis FastAPI).  
Jej zadaniem jest:

- pobieranie z mocka informacji o dostępnych migawkach (snapshotach) danych ERP/MES,
- synchronizowanie tych informacji z bazą danych backendu,
- udostępnianie spójnego API dla frontendu i agentów AI,
- przygotowanie fundamentu pod dalsze przetwarzanie danych (RAG, streszczenia, testy),
- zapewnienie zadań asynchronicznych Celery do okresowej synchronizacji.

Mock ERP/MES udostępnia metadane o plikach (JSON-y, dokumenty) i same pliki przez HTTP – backend **nigdy nie czyta dysku mocka bezpośrednio**, tylko korzysta z API HTTP.

---

## 2. Architektura modułu

W dużym uproszczeniu przepływ wygląda tak:

1. **Mock ERP/MES (FastAPI)** – serwis wystawia endpointy:
   - `/manifest` – lista wersji ERP/MES i informacja o „latest”,
   - `/erp` – listing plików dla migawki ERP,
   - `/mes` – listing plików dla migawki MES,
   - `/files` – pobieranie pojedynczych plików (JSON/PDF itd.).
2. **Backend Django – aplikacja `erp_mes`**:
   - integruje się z mockiem przez klienta HTTP `MockErpMesClient`,
   - zapisuje metadane snapshotów w modelu `ErpMesSnapshot`,
   - loguje przebieg synchronizacji w modelu `SnapshotSyncLog`,
   - wystawia własne endpointy REST `/api/erp-mes/...`.
3. **Pozostałe moduły backendu** (np. `documents/`, `agents/`):
   - korzystają z API `erp_mes` i z zadań Celery, aby pobierać i przetwarzać dane,
   - nie gadamy bezpośrednio z mockiem, tylko przez `erp_mes`.

Dzięki temu integracja z mockiem jest **skupiona w jednym miejscu**, a reszta systemu (RAG, streszczenia, testy, frontend) widzi już tylko ujednolicone API backendu.

---

## 3. Modele danych

### 3.1. `ErpMesSnapshot`

Reprezentuje pojedynczą migawkę danych z mocka dla danego strumienia („erp” lub „mes”) i konkretnej daty.

**Najważniejsze pola:**

- `stream` – `CharField`, jedno z: `"erp"` lub `"mes"` (pole z choices),
- `version_date` – `DateField`, np. `2026-02-22`,
- `is_latest` – `BooleanField`, informacja czy ta migawka jest aktualnie najnowsza (zgodnie z manifestem mocka),
- `files` – `JSONField`, cache listingu plików z mocka:
  ```json
  [
    { "name": "work_orders.json", "size": 12345 },
    { "name": "bom_components.json", "size": 67890 }
  ]
  ```
- `created_at`, `updated_at` – znaczniki czasu.

**Konwencje i uwagi:**

- `(stream, version_date)` musi być unikalne (`unique_together`),
- dla każdego `stream` dokładnie jedna migawka powinna mieć `is_latest = True` (pilnuje tego logika synchronizacji),
- `files` jest cachem – zawsze można go odświeżyć z mocka, jeśli coś się zmieni.

### 3.2. `SnapshotSyncLog`

Model służący do logowania przebiegu synchronizacji z mockiem.

**Najważniejsze pola:**

- `stream` – `"erp"` lub `"mes"`,
- `version_date` – data migawki, której dotyczy log,
- `snapshot` – `ForeignKey` do `ErpMesSnapshot` (może być `null`, np. w razie błędu przed utworzeniem snapshotu),
- `status` – `"pending"`, `"success"`, `"failed"`,
- `started_at`, `finished_at` – znaczniki czasu,
- `error_message` – opis błędu, jeśli `status="failed"`.

Logi można wykorzystać w panelu admina, logach serwera lub przy debugowaniu Celery.

---

## 4. Klient HTTP do mock ERP/MES – `MockErpMesClient`

Logika komunikacji z mockiem jest wydzielona do klasy `MockErpMesClient` (w pliku `erp_mes/services.py`).  
Dzięki temu:

- backend nie rozrzuca „gołych” wywołań HTTP po widokach,
- łatwiej jest mockować/zastąpić klienta w testach,
- można w jednym miejscu wprowadzić cache (Redis) i obsługę błędów.

### 4.1. Konfiguracja

Klient używa zmiennych środowiskowych i ustawień Django:

- `MOCK_API_BASE` – bazowy URL do mock ERP/MES, np. `http://mock-erp-mes:8001`,
- `REDIS_URL` – URL do brokera Redis (przydatny przy cachowaniu).

W kodzie klienta:

```python
self.base_url = getattr(settings, "MOCK_API_BASE", "").rstrip("/")
```

### 4.2. Metody klienta

Najważniejsze metody:

- `get_manifest()` – pobiera `GET /manifest` z mocka, z cache (Redis) na ~5 minut,
- `get_stream_listing(stream, date)` – pobiera listing plików:
  - dla `stream="erp"` → `GET /erp?date=YYYY-MM-DD`,
  - dla `stream="mes"` → `GET /mes?date=YYYY-MM-DD`,
  - wynik: `{ "date": "2025-12-15", "files": [ { "name", "size" }, ... ] }`,
  - wynik jest cachowany na kilka minut,
- `get_file_bytes(stream, name, date)` – pobiera plik z `/files` jako bajty:
  - dla `stream="docs"` → PDF/plik z `data/docs/...`,
  - dla `stream="erp"`/`"mes"` → plik z danej migawki (wymaga `date`).

Klient sam rzuca wyjątek, jeśli HTTP zwróci błąd (`response.raise_for_status()` w `_get`).

---

## 5. Endpointy API w `erp_mes`

Aplikacja `erp_mes` wystawia endpointy REST pod prefiksem:

```text
/api/erp-mes/
```

Wszystkie endpointy wymagają **uwierzytelnienia JWT** (tak jak reszta backendu), z wyjątkiem ewentualnych publicznych healthchecków (standardowo ich tu nie ma). Synchronizacja jest dodatkowo ograniczona do adminów.

### 5.1. Lista wszystkich snapshotów

**URL:** `GET /api/erp-mes/snapshots/`  
**Opis:** Zwraca listę wszystkich snapshotów ERP i MES zapisanych w bazie.  
**Zastosowanie:** frontend (widok przeglądu migawek), testy, debug.

**Przykładowa odpowiedź:**

```json
[
  {
    "id": 1,
    "stream": "erp",
    "version_date": "2025-12-15",
    "is_latest": false
  },
  {
    "id": 2,
    "stream": "erp",
    "version_date": "2026-03-30",
    "is_latest": true
  },
  {
    "id": 3,
    "stream": "mes",
    "version_date": "2025-12-15",
    "is_latest": false
  }
]
```

### 5.2. Lista snapshotów dla konkretnego strumienia

**URL:** `GET /api/erp-mes/{stream}/snapshots/`  
`{stream}` ∈ `{ "erp", "mes" }`

**Opis:** Zwraca listę snapshotów tylko dla wybranego strumienia.  
**Zastosowanie:** wybór wersji danych ERP/MES dla konkretnego widoku/analizy.

### 5.3. Detal snapshotu + listing plików

**URL:** `GET /api/erp-mes/{stream}/snapshots/{date}/files/`  
`date` w formacie `YYYY-MM-DD`.

**Opis:** Zwraca obiekt `ErpMesSnapshot` wraz z cached listą plików z `files`.  
Jeśli `files` jest puste, logika może (w przyszłości) wymusić odświeżenie listingu z mocka.

**Przykładowa odpowiedź:**

```json
{
  "id": 2,
  "stream": "erp",
  "version_date": "2026-03-30",
  "is_latest": true,
  "files": [
    { "name": "work_orders.json", "size": 12345 },
    { "name": "bom_components.json", "size": 67890 }
  ],
  "created_at": "2025-11-25T20:00:00Z",
  "updated_at": "2025-11-25T20:05:00Z"
}
```

### 5.4. Ręczna synchronizacja z mockiem

**URL:** `POST /api/erp-mes/snapshots/sync/`  
**Uprawnienia:** tylko admin (`IsAdminUser`).

**Opis:**

1. Pobiera manifest z mocka (`/manifest`),
2. Dla każdego strumienia (`erp`, `mes`):
   - resetuje `is_latest` dla starej najnowszej migawki,
   - iteruje po wszystkich datach w manifestcie,
   - dla każdej daty:
     - tworzy lub aktualizuje `ErpMesSnapshot`,
     - ustawia `is_latest=True` tylko dla tej daty, która jest oznaczona jako „latest” w manifestcie,
     - pobiera listing plików z mocka i zapisuje w `files`,
     - tworzy wpis `SnapshotSyncLog` typu `success`.

**Zastosowanie:**

- ręczne odpalenie SYNC z poziomu backendu, gdy chcemy natychmiast odświeżyć snapshoty (np. podczas demo),
- fallback, jeśli Celery Beat nie działa lub jest wyłączony.

### 5.5. Pobieranie pliku JSON jako API

**URL:** `GET /api/erp-mes/{stream}/snapshots/{date}/json/{filename}/`  

**Opis:**

- używa `MockErpMesClient.get_file_bytes(...)`, aby pobrać plik z mocka,
- zakłada, że plik jest JSON-em,
- dekoduje bajty do UTF-8 i robi `json.loads(...)`,
- zwraca JSON w odpowiedzi API.

**Przykład użycia:**

- frontendowy widok danych „Work Orders”,
- agent AI, który potrzebuje surowej struktury danych do zbudowania promptu.

---

## 6. Zadania Celery w `erp_mes`

Aplikacja `erp_mes` dostarcza podstawowe zadania Celery, które będą rozwijane przez agenty AI i inne moduły.

### 6.1. `sync_erp_mes_snapshots_task`

**Cel:** asynchroniczna wersja endpointu `POST /api/erp-mes/snapshots/sync/`.

**Działanie:**

1. Tworzy instancję `MockErpMesClient`.
2. Pobiera manifest z mocka (`get_manifest()`).
3. Dla `erp` i `mes`:
   - resetuje `is_latest` dla starej najnowszej migawki,
   - iteruje po datach w manifestcie,
   - tworzy/aktualizuje `ErpMesSnapshot`,
   - pobiera listing plików (`get_stream_listing(...)`),
   - zapisuje `files`,
   - dodaje wpis `SnapshotSyncLog` o statusie `success` (lub `failed` w przyszłych rozszerzeniach).

**Typowe wywołanie:**

- ręcznie z Django shell, np.:  
  `sync_erp_mes_snapshots_task.delay()`
- cyklicznie z Celery Beat, np. co 10–15 minut lub raz na godzinę.

### 6.2. `fetch_erp_mes_json_file_task`

**Cel:** pobranie JSON-a z mocka i zwrócenie go jako dict (np. do dalszego przetwarzania).

**Działanie:**

1. Wywołuje `get_file_bytes(stream, name, date)`,
2. Próbuje zdekodować z UTF-8 i zrobić `json.loads(...)`,
3. Zwraca słownik (albo `None` w razie błędu).

**Zastosowanie:**

- w przyszłości: użyć tego taska jako element pipeline’u:
  - pobierz JSON → zapisz jako dokument w `documents/` → odpal agenta RAG.

---

## 7. Integracja z modułem `documents/` (RAG)

Aplikacja `erp_mes` jest fundamentem pod późniejsze moduły RAG.  
Docelowo moduł `documents/` będzie zawierał model `Document` z polami:

- `source` – np. `"MOCK_ERP"`, `"MOCK_MES"`, `"MOCK_DOCS"`, `"USER_UPLOAD"`,
- pola identyfikujące pochodzenie z mocka: `mock_stream`, `mock_version_date`, `mock_filename`,
- `stored_file` – lokalna kopia pliku (PDF/JSON),
- metadane (tytuł, opis, produkt, itp.).

**Przykładowy scenariusz integracyjny:**

1. SYNC z mockiem (manualny lub przez Celery Beat) odświeża `ErpMesSnapshot`.
2. Osobny endpoint / task w `documents/` pobiera listę plików z danego snapshotu (`ErpMesSnapshot.files`).
3. Dla każdego wybranego pliku:
   - tworzy rekord `Document` z odniesieniem do snapshotu (`stream`, `version_date`, `filename`),
   - zleca Celery taskowi pobranie pliku z mocka i zapis do `stored_file`,
   - w kolejnym kroku pipeline’u (kolejny task) parsuje plik, dzieli na chunki, zapisuje embeddingi.

Dzięki temu `erp_mes` pozostaje odpowiedzialny tylko za „co i gdzie istnieje w mocku” oraz za bazowy sync i fetch JSON; logika RAG powinna być na następnym poziomie (od strony dokumentów i agentów).

---

## 8. Jak z tym współpracować (dla człowieka i chatbota)

### 8.1. Typowe scenariusze pracy

1. **Dodano nową migawkę w mocku (np. 2026-03-30):**
   - mock aktualizuje `manifest.json`,
   - backend (Celery Beat) odpala `sync_erp_mes_snapshots_task`,
   - w DB pojawia się nowy `ErpMesSnapshot`,
   - frontend może pokazać nową wersję w UI,
   - agent RAG (przez `documents/`) może zaciągnąć nowe pliki.

2. **Developer chce szybko przetestować integrację:**
   - wykonuje `POST /api/erp-mes/snapshots/sync/` (jako admin),
   - sprawdza `GET /api/erp-mes/erp/snapshots/`,
   - wybiera datę i odpytuje `GET /api/erp-mes/erp/snapshots/{date}/files/`,
   - na końcu `GET /api/erp-mes/erp/snapshots/{date}/json/work_orders.json/`.

3. **Agent lub inny backendowy moduł potrzebuje surowych danych JSON:**
   - używa taska Celery `fetch_erp_mes_json_file_task`,
   - działa asynchronicznie, nie blokuje requestu HTTP,
   - wynik JSON może zapisać do innej tabeli lub przekazać do modelu LLM.

### 8.2. Q&A w stylu „dla chatbota”

**P: Czy backend czyta pliki ERP/MES bezpośrednio z dysku mocka?**  
O: Nie. Backend komunikuje się z mock ERP/MES wyłącznie przez HTTP (endpointy `/manifest`, `/erp`, `/mes`, `/files`). Dysk mocka jest zamontowany tylko w kontenerze mock.

**P: Gdzie zobaczę jakie snapshoty są dostępne?**  
O: Użyj endpointu `GET /api/erp-mes/snapshots/` (lub `/api/erp-mes/{stream}/snapshots/` dla konkretnego strumienia). Tam znajdziesz daty i flagę `is_latest`.

**P: Jak wymusić natychmiastową synchronizację z mockiem?**  
O: Wywołaj `POST /api/erp-mes/snapshots/sync/` jako admin. To endpoint manualny, odpowiednik taska Celery `sync_erp_mes_snapshots_task`.

**P: Jak agent AI ma dostać surowy JSON z ERP/MES?**  
O: Może użyć endpointu `GET /api/erp-mes/{stream}/snapshots/{date}/json/{filename}/` albo taska `fetch_erp_mes_json_file_task` (w pipeline Celery). Oba korzystają z tego samego klienta HTTP do mocka.

**P: Gdzie wpiąć logikę RAG (parsowanie, embeddingi)?**  
O: W osobnej aplikacji `documents/`/`ai_agents/`. `erp_mes` zapewnia tylko informację „co jest dostępne w mocku” oraz podstawowy sync i fetch JSON; logika RAG powinna być na następnym poziomie (od strony dokumentów i agentów).

---

## 9. Dalszy rozwój modułu

Miejsca przewidziane pod rozbudowę (dla Ciebie lub dla agentów):

- dodanie wsparcia dla checksum / `updated_at` (wykrywanie zmian między snapshotami),
- rozróżnienie typów plików (PDF, JSON, CSV) i decyzja, co trafia do RAG,
- rozbudowa `SnapshotSyncLog` o statusy szczegółowe (np. częściowy sukces),
- dodatkowe endpointy do reindeksacji tylko zmienionych dokumentów,
- bardziej zaawansowany cache i obsługa błędów sieci (retry, exponential backoff).

Aplikacja `erp_mes` jest fundamentem: ma dostarczyć spójny, stabilny kontrakt na dane ERP/MES, tak aby reszta systemu (w tym agenci AI) mogła się na nim oprzeć bez konieczności zaglądania „jak działa mock pod spodem”.
