# Aplikacja `documents` – dokumenty pod RAG i upload użytkownika

## 1. Cel i rola modułu

Aplikacja `documents` jest centralnym miejscem do pracy z **plikiem jako dokumentem** w systemie Proscientia.  
To tutaj łączą się trzy światy:

1. **Dane z mock ERP/MES** (pliki JSON/PDF pobierane przez `erp_mes`),
2. **Mockowe dokumenty techniczne** (PDF-y z katalogu `docs/` serwisu mock),
3. **Pliki użytkowników** (np. ich własne specyfikacje, procedury, dokumentacja).

Główne zadania modułu:

- przechowywanie informacji o dokumentach (źródło, tytuł, opis, tagi, metadane),
- zarządzanie fizycznym plikiem (przez `FileField` i `MEDIA_ROOT`),
- wystawianie prostego API do listowania i pobierania dokumentów,
- obsługa uploadu plików przez użytkowników,
- integracja z mock ERP/MES – tworzenie dokumentów z istniejących plików w snapshotach,
- dostarczanie zadań Celery, które ściągają pliki z mocka i parsują dokumenty (fundament pod RAG, streszczenia i testy).

W skrócie: **`documents` trzyma wiedzę o tym, jakie dokumenty mamy i gdzie leżą**, a także pomaga w ich przygotowaniu do analizy przez agentów AI.

---

## 2. Jak FileField działa w Django

W modelu `Document.file` używamy `FileField`. Ważne jest zrozumienie, co trafia do bazy danych, a co na dysk:

- **W bazie danych** przechowywana jest tylko **ścieżka do pliku** (np. `documents/2025/11/25/spec_pb560.pdf`),
- **Fizyczny plik** jest zapisywany w katalogu `MEDIA_ROOT` (np. `/app/media/documents/...`).

To dokładnie to zachowanie, którego potrzebujemy:

- baza nie trzyma binarnych danych pliku,
- pliki są przechowywane na dysku serwera (lub na wolumenie dockera / S3 w przyszłości),
- aplikacja może budować pełne URL-e do plików na podstawie ścieżki z bazy i konfiguracji `MEDIA_URL`.

---

## 3. Model `Document`

### 3.1. Pola i ich znaczenie

Model `Document` reprezentuje **jeden dokument** w systemie (PDF, JSON, inny plik).  
Najważniejsze pola:

```python
class Document(models.Model):
    SOURCE_MOCK_DOCS = "MOCK_DOCS"
    SOURCE_MOCK_ERP = "MOCK_ERP"
    SOURCE_MOCK_MES = "MOCK_MES"
    SOURCE_USER_UPLOAD = "USER_UPLOAD"
```

- `source` – skąd pochodzi dokument:
  - `MOCK_DOCS` – dokument techniczny z katalogu `docs/` mocka,
  - `MOCK_ERP` – plik z mock ERP (np. snapshot `work_orders.json`),
  - `MOCK_MES` – plik z mock MES,
  - `USER_UPLOAD` – plik wrzucony przez użytkownika (frontend / admin).

Pozostałe pola:

- `title` – tytuł dokumentu, wyświetlany w UI,
- `description` – opis dokumentu,
- `content_type` – typ MIME (np. `application/pdf`, `application/json`),
- `tags` – lista tagów (`JSONField`), np. `["ventilator", "safety", "pb560"]`,
- `uploaded_by` – użytkownik, który wrzucił dokument (dla mockowych może być `null`),
- `file` – `FileField`, ścieżka do fizycznego pliku w `MEDIA_ROOT`,
- `mock_stream` – `"erp"`, `"mes"` lub `"docs"`:
  - dla dokumentów z ERP/MES: `"erp"` / `"mes"`,
  - dla dokumentów z `docs/`: `"docs"`,
- `mock_version_date` – data snapshotu ERP/MES (`DateField`), używana dla `MOCK_ERP` / `MOCK_MES`,
- `mock_filename` – nazwa pliku po stronie mocka:
  - dla ERP/MES: np. `"work_orders.json"`,
  - dla docs: np. `"ventilator_pb560/spec_pb560_overview.pdf"`,
- `created_at`, `updated_at` – znaczniki czasu,
- `is_active` – prosta flaga soft-delete / wyłączenia dokumentu.

### 3.2. Właściwości pomocnicze

W modelu są proste property ułatwiające logikę:

- `is_user_upload` – `True`, jeśli `source == USER_UPLOAD`,
- `is_mock_doc` – `True`, jeśli `source == MOCK_DOCS`,
- `is_mock_erp_mes` – `True`, jeśli `source` jest jednym z `MOCK_ERP` / `MOCK_MES`.

Te property są wykorzystywane m.in. w tasku Celery `fetch_and_store_file_task`.

---

## 4. Serializery

### 4.1. `DocumentSerializer`

Służy do **odczytu** dokumentu (lista, detail).  
Pola:

- `id`, `source`, `title`, `description`, `content_type`, `tags`,
- `uploaded_by_email` – email użytkownika, który wrzucił dokument (albo `null`),
- `file_url` – pełny URL do pliku (albo `null`, jeśli plik nie został jeszcze pobrany z mocka),
- `mock_stream`, `mock_version_date`, `mock_filename`,
- `created_at`, `updated_at`.

`file_url` jest wyliczany dynamicznie na podstawie `request.build_absolute_uri(...)`, więc działa poprawnie zarówno lokalnie, jak i na serwerze.

### 4.2. `DocumentUploadSerializer`

Służy do **uploadu pliku przez użytkownika**.  
Pola wejściowe:

- `file` – wymagany,
- `title` – opcjonalny; jeśli brak, dokument użyje `file.name`,
- `description` – opcjonalny,
- `tags` – opcjonalne.

W `create()`:

- pobiera użytkownika z `request.user`,
- tworzy nowy `Document` z:
  - `source=USER_UPLOAD`,
  - `title` (od użytkownika lub nazwa pliku),
  - `description`, `tags`,
  - `uploaded_by=user`,
  - `file=file`,
  - `content_type` (jeśli dostępny z obiektu pliku).

### 4.3. `DocumentFromErpMesSerializer`

Serializer do tworzenia dokumentu z pliku ERP/MES:

Pola wejściowe:

- `stream` – `"erp"` lub `"mes"`,
- `version_date` – data snapshotu (`YYYY-MM-DD`),
- `filename` – nazwa pliku w snapshotcie,
- `title` – opcjonalny tytuł (domyślnie `filename`),
- `description`, `tags` – opcjonalne.

W `create()`:

- na podstawie `stream` wybiera `source`:
  - `erp` → `MOCK_ERP`,
  - `mes` → `MOCK_MES`,
- tworzy `Document` z:
  - `source` ustawionym na `MOCK_ERP` lub `MOCK_MES`,
  - `mock_stream` = `stream`,
  - `mock_version_date` = podana data,
  - `mock_filename` = podany `filename`,
  - `title`, `description`, `tags`.

Na tym etapie **nie ma jeszcze fizycznego pliku** – jest tylko informacja, skąd go potem pobrać.

---

## 5. Endpointy API

Wszystkie endpointy `documents` wystawione są pod prefiksem:

```text
/api/documents/
```

i wymagają autoryzacji JWT (`IsAuthenticated`).

### 5.1. Lista dokumentów

**URL:** `GET /api/documents/`  
**Opis:** Zwraca listę wszystkich aktywnych dokumentów z możliwością filtrowania.  
**Filtrowanie:**

- `?source=MOCK_ERP` – tylko dokumenty z ERP,
- `?stream=erp` / `?stream=mes` – filtrowanie po strumieniu mocka,
- `?version_date=2025-12-15` – dokumenty z określonej daty snapshotu (ERP/MES).

Przykładowa odpowiedź:

```json
[
  {
    "id": 1,
    "source": "USER_UPLOAD",
    "title": "Specyfikacja klienta",
    "description": "",
    "content_type": "application/pdf",
    "tags": ["client", "spec"],
    "uploaded_by_email": "user@example.com",
    "file_url": "http://localhost:8000/media/documents/2025/11/25/spec.pdf",
    "mock_stream": "",
    "mock_version_date": null,
    "mock_filename": "",
    "created_at": "2025-11-25T19:00:00Z",
    "updated_at": "2025-11-25T19:00:00Z"
  }
]
```

### 5.2. Szczegóły dokumentu

**URL:** `GET /api/documents/<id>/`  
**Opis:** Zwraca jeden dokument (te same pola co w liście).

### 5.3. Upload pliku przez użytkownika

**URL:** `POST /api/documents/upload/`  
**Body:** `multipart/form-data`

Pola:

- `file` – wymagany,
- `title` – opcjonalny,
- `description` – opcjonalny,
- `tags` – opcjonalne (np. JSON w stringu lub obsługiwane przez front).

Przykład (curl):

```bash
curl -X POST http://localhost:8000/api/documents/upload/   -H "Authorization: Bearer <ACCESS_TOKEN>"   -F "file=@/path/to/file.pdf"   -F "title=Test PDF"   -F "description=Dokument testowy"
```

Działanie endpointu:

1. `DocumentUploadSerializer` tworzy rekord `Document` z `source=USER_UPLOAD` i zapisuje plik do `MEDIA_ROOT` przez `FileField`.
2. Od razu zlecany jest task Celery `parse_document_task(document_id)` – fundament pod późniejsze parsowanie treści dokumentu.

### 5.4. Tworzenie dokumentu z ERP/MES

**URL:** `POST /api/documents/from-erp-mes/`  
**Body:** JSON:

```json
{
  "stream": "erp",
  "version_date": "2025-12-15",
  "filename": "work_orders.json",
  "title": "Work Orders 2025-12-15",
  "description": "Zlecenia pracy na dzień 2025-12-15",
  "tags": ["erp", "work_orders"]
}
```

Działanie endpointu:

1. `DocumentFromErpMesSerializer` tworzy rekord `Document` z odpowiednim `source` (`MOCK_ERP`/`MOCK_MES`) i uzupełnia `mock_stream`, `mock_version_date`, `mock_filename`.
2. Zlecany jest task Celery `fetch_and_store_file_task(document_id)` – zadanie pobiera fizyczny plik z mocka i zapisuje go do `file` w modelu.

Na tym etapie dokument ma:

- metadane (źródło, snapshot, filename),
- fizyczny plik zapisany w `MEDIA_ROOT` (po wykonaniu taska Celery),
- jest gotowy do dalszego parsowania / indeksowania / użycia przez RAG.

---

## 6. Taski Celery – integracja z mockiem i RAG

### 6.1. `fetch_and_store_file_task`

**Sygnatura:**

```python
@shared_task
def fetch_and_store_file_task(document_id: int) -> None:
    ...
```

**Cel:** dla dokumentów pochodzących z mocka (`MOCK_DOCS`, `MOCK_ERP`, `MOCK_MES`) pobiera fizyczny plik z mocka i zapisuje go do `Document.file`.

**Działanie:**

1. Pobiera `Document` z bazy po `document_id`.
2. Sprawdza, czy `doc.is_mock_doc` lub `doc.is_mock_erp_mes`. Jeśli nie – wychodzi.
3. Tworzy `MockErpMesClient` (z modułu `erp_mes.services`).
4. W zależności od źródła:
   - `MOCK_ERP` / `MOCK_MES`:
     - używa `stream = doc.mock_stream` (`"erp"` lub `"mes"`),
     - używa `date = doc.mock_version_date` (sformatowane jako `YYYY-MM-DD`),
     - używa `name = doc.mock_filename`,
     - wywołuje `client.get_file_bytes(stream, name, date)`.
   - `MOCK_DOCS`:
     - używa `stream = "docs"`,
     - używa `name = doc.mock_filename`,
     - `date` jest `None` (mock docs nie używają daty).
5. Zapisuje bajty do `Document.file`:
   - generuje nazwę (np. `doc.mock_filename`),
   - `doc.file.save(file_name, ContentFile(content_bytes), save=True)`.

Po tym tasku dokument ma fizyczny plik w `MEDIA_ROOT` i jest gotowy do dalszej pracy (np. parsowania).

### 6.2. `parse_document_task`

**Sygnatura:**

```python
@shared_task
def parse_document_task(document_id: int) -> None:
    ...
```

**Cel:** placeholder pod parsowanie dokumentów – miejsce, gdzie Twój kolega dołoży logikę RAG/LLM.

**Aktualne działanie:**

- sprawdza, czy `Document` istnieje,
- loguje informację, że parsowanie zostało wywołane (źródło, tytuł).

**Docelowo:**

- dla PDF:
  - odczytać plik z `doc.file`,
  - wyciągnąć tekst (np. przy pomocy biblioteki `pdfplumber` / `PyPDF2` / zewnętrznego serwisu),
  - podzielić na chunki,
  - zapisać chunki w osobnej tabeli (np. `DocumentChunk`) wraz z embeddingami (pgvector),
- dla JSON:
  - przekształcić strukturę na tekst lub ustrukturyzowane fragmenty,
  - podobnie jak dla PDF – przygotować kontekst do RAG.

Dalej w pipeline można wywoływać inne taski (np. `generate_summary_task`, `generate_quiz_task`), które będą tworzyć streszczenia i testy wiedzy na bazie dokumentu.

---

## 7. Typowe scenariusze użycia

### 7.1. Użytkownik wrzuca własny dokument

1. Frontend wywołuje `POST /api/documents/upload/` z plikiem i metadanymi.
2. Backend zapisuje dokument do bazy i plik do `MEDIA_ROOT`.
3. Celery odpala `parse_document_task(document_id)` – do dalszego przetwarzania.

### 7.2. Import dokumentu z ERP/MES

1. Frontend pokazuje listę plików z `ErpMesSnapshot.files` (z modułu `erp_mes`).
2. Użytkownik wybiera plik (np. `work_orders.json`) i klika „Dodaj do dokumentów”.
3. Frontend wywołuje `POST /api/documents/from-erp-mes/` z `stream`, `version_date`, `filename`.
4. Powstaje `Document` z informacją skąd pobrać plik.
5. Celery task `fetch_and_store_file_task` pobiera plik z mocka i zapisuje go lokalnie.
6. Opcjonalnie można od razu odpalić `parse_document_task(document_id)`.

### 7.3. Dokumenty mock docs (PDF-y z katalogu `docs/`)

Podobny scenariusz jak dla ERP/MES:

1. Backend (lub specjalny endpoint) tworzy `Document` z `source=MOCK_DOCS` i `mock_filename`,
2. Task `fetch_and_store_file_task` pobiera PDF z `/files?stream=docs&name=...`,
3. Task `parse_document_task` przygotowuje tekst do RAG.

---

## 8. Współpraca z agentami AI

Dla Twojego kolegi (i dla agentów, np. ChatGPT/Gemini), `documents` jest idealnym punktem wejścia:

- **do enumerowania dostępnych dokumentów** (GET `/api/documents/`, filtr po `source`, `stream`, `version_date`),
- **do pobierania zawartości dokumentów** (przez `file_url` lub lokalny dostęp do `MEDIA_ROOT`),
- **do inicjowania pipeline’u RAG** (przez wywołanie tasków Celery z ID dokumentu).

Przykład workflow dla agenta „streszczeniowego”:

1. Agent wybiera dokument z listy (`documents` API).
2. Agent wywołuje (bezpośrednio lub pośrednio) `parse_document_task(document_id)`.
3. Task parsuje dokument → Twój kolega doda logikę generowania streszczenia/quizu i zapisze wynik do osobnych modeli (np. `SummaryArtifact`, `QuizArtifact`).

Aplikacja `documents` jest więc **fundamentem**: trzyma stan dokumentów, ich pochodzenie oraz fizyczne pliki, ale nie definiuje logiki samego RAG–a (to trafi do kolejnych modułów).

---

## 9. Podsumowanie

- `documents` zapewnia **jednolity model dokumentu** niezależnie od źródła (mock ERP, mock MES, mock docs, user upload),
- pliki **nie są trzymane w bazie**, tylko na dysku w `MEDIA_ROOT` – w bazie mamy ścieżki i metadane,
- API:
  - `GET /api/documents/` – lista dokumentów,
  - `GET /api/documents/<id>/` – szczegóły,
  - `POST /api/documents/upload/` – upload pliku użytkownika,
  - `POST /api/documents/from-erp-mes/` – utworzenie dokumentu na podstawie pliku w mock ERP/MES,
- Celery:
  - `fetch_and_store_file_task` – pobiera plik z mocka i zapisuje do FileField,
  - `parse_document_task` – miejsce na logikę parsowania i przygotowania danych pod RAG.

Całość jest zaprojektowana tak, abyś mógł dalej spokojnie rozwijać:

- moduł `ai_agents` (streszczenia, quizy, RAG),
- integrację z frontendem (lista dokumentów, upload, podgląd),
- pipeline Celery (parsowanie, embeddingi, generowanie odpowiedzi).

