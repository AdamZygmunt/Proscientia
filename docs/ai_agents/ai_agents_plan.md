# Plan integracji agentów AI w systemie Proscientia

## 1. Kontekst i aktualny stan systemu

System Proscientia składa się z kilku głównych komponentów backendowych, które tworzą fundament pod wdrożenie agentów AI:

- **`users`** – moduł uwierzytelniania i autoryzacji:
  - niestandardowy model użytkownika z rolami,
  - JWT (SimpleJWT) do ochrony API,
  - podstawowy podział uprawnień (np. admin vs użytkownik).

- **`erp_mes`** – integracja z mockowym systemem ERP/MES (FastAPI):
  - modele `ErpMesSnapshot` (migawki danych) i `SnapshotSyncLog` (logi synchronizacji),
  - klient HTTP `MockErpMesClient` do komunikacji z mock ERP/MES (`/manifest`, `/erp`, `/mes`, `/files`),
  - endpointy REST do listowania snapshotów, list plików i manualnego sync,
  - zadanie Celery `sync_erp_mes_snapshots_task`, które okresowo aktualizuje migawki,
  - wstępny szkic zadania `fetch_erp_mes_json_file_task`.

- **`documents`** – moduł dokumentów i uploadu użytkownika:
  - model `Document` ze źródłami:
    - dane z mock ERP (`MOCK_ERP`),
    - dane z mock MES (`MOCK_MES`),
    - dokumenty techniczne z mock (`MOCK_DOCS`),
    - dokumenty wrzucane przez użytkowników (`USER_UPLOAD`),
  - powiązanie z mockiem przez pola: `mock_stream`, `mock_version_date`, `mock_filename`,
  - `FileField`, który zapisuje pliki w `MEDIA_ROOT` (w bazie przechowywana jest ścieżka),
  - endpointy:
    - `GET /api/documents/` – lista dokumentów z filtrowaniem,
    - `GET /api/documents/<id>/` – szczegóły,
    - `POST /api/documents/upload/` – upload pliku użytkownika,
    - `POST /api/documents/from-erp-mes/` – utworzenie dokumentu z pliku z ERP/MES,
  - zadania Celery:
    - `fetch_and_store_file_task` – pobranie pliku z mocka i zapis do `Document.file`,
    - `parse_document_task` – placeholder pod parsowanie dokumentów i przygotowanie pod RAG.

- **Infrastruktura asynchroniczna**:
  - Celery skonfigurowane z aplikacją Django (moduł `proscientia.celery_app`),
  - Redis jako broker i backend wyników,
  - Celery Beat jako scheduler (np. periodyczna synchronizacja ERP/MES).

Szczegółowe opisy poszczególnych aplikacji (modele, endpointy, schematy danych) znajdują się w dedykowanych dokumentacjach (`docs/backend/erp_mes.md`, `docs/backend/documents.md`, `docs/erp_mes_data/...`). Niniejszy dokument skupia się na projektowanym podejściu do agentów AI oraz na tym, jak rozszerzyć istniejącą infrastrukturę Celery/Redis o logikę związaną z przetwarzaniem dokumentów i komunikacją z zewnętrznym API modeli językowych.

---

## 2. Założenia dotyczące agentów AI

### 2.1. Charakterystyka agentów

Agenci AI mają realizować zadania związane z przetwarzaniem wiedzy zgromadzonej w dokumentach i danych ERP/MES, m.in.:

- generowanie streszczeń dokumentów (lub zestawu dokumentów),
- odpowiadanie na pytania użytkownika w oparciu o RAG (retrieval-augmented generation),
- generowanie testów wiedzy (MCQ/SCQ) na podstawie dokumentacji technicznej i aktualnego stanu systemu,
- budowanie raportów/audytów (np. porównanie dwóch snapshotów ERP/MES).

Agenci będą działać **asynchronicznie**, korzystając z Celery i kolejki Redis, oraz komunikować się z zewnętrznym API modeli językowych (np. OpenAI Assistants).

### 2.2. Główne zasady projektowe

1. **Brak ciężkich obliczeń w request/response** – frontend nigdy nie czeka bezpośrednio na wynik długiego zadania (parsowanie PDF, embedowanie, generowanie dużego streszczenia). Zamiast tego tworzone jest zadanie Celery, a frontend obserwuje status.

2. **Wyraźne oddzielenie warstw:**

   - `erp_mes` – odpowiedzialne za to, *co* i *gdzie* jest w mock ERP/MES,
   - `documents` – odpowiedzialne za to, *jakie dokumenty mamy w systemie* i *gdzie leżą fizyczne pliki*,
   - moduł agentów (np. `ai_agents` / `knowledge`) – odpowiedzialny za:
     - parsowanie i ekstrakcję wiedzy,
     - tworzenie embeddingów i zapisywanie do bazy,
     - orkiestrację wywołań zewnętrznego API (OpenAI itp.),
     - przechowywanie wyników (streszczenia, testy, audyty).

3. **Taski Celery jako „klocki” pipeline’u** – pojedyncze zadania są małe, dobrze zdefiniowane i łatwe do łączenia w pipeline (chain, group, chord).

4. **Idempotentność i powtarzalność** – taski powinny być tak projektowane, aby można je było uruchomić ponownie bez „psucia” stanu (np. parsowanie nadpisuje stare wyniki lub tworzy nową wersję).

5. **Obserwowalność** – logowanie w taskach oraz opcjonalne modele „logów agentów” ułatwią debugowanie i analizę.

---

## 3. Proponowana struktura modułu agentów

Docelowo zaleca się utworzenie osobnej aplikacji backendowej, np. `ai_agents` lub `knowledge`, która będzie zawierała:

- modele artefaktów generowanych przez agentów,
- definicje tasków Celery tworzących pipeline przetwarzania,
- ewentualne endpointy REST do odczytu wyników.

### 3.1. Przykładowe modele (wysoki poziom)

- `DocumentChunk` – fragment dokumentu używany w RAG:
  - `document` (FK do `Document`),
  - `chunk_index`, `text`, `embedding` (np. pole vector w pgvector),
  - metadane (strona, sekcja, typ treści).

- `SummaryArtifact` – streszczenie dokumentu lub zestawu dokumentów:
  - `document` (FK lub lista odniesień),
  - `summary_text`,
  - opcjonalne: kluczowy kontekst użyty do streszczenia,
  - status generowania (pending/success/failed).

- `QuizArtifact` – test wiedzy:
  - odniesienie do dokumentów,
  - lista pytań (jako JSON),
  - metadane (poziom trudności, tematyka),
  - status generowania.

- `AgentJob` (opcjonalne) – ogólny model „zadania agenta”:
  - typ zadania (summary, quiz, QA),
  - parametry wejściowe (JSON),
  - powiązane dokumenty,
  - identyfikator taska Celery,
  - status, log błędów, timestampy.

Szczegółowa struktura może być dostosowana do faktycznych potrzeb, ale ważne, aby istniało miejsce na trwałe przechowywanie wyników pracy agentów.

---

## 4. Taski Celery jako fundament agentów

### 4.1. Warstwa niskopoziomowa – operacje na dokumentach

Na najniższym poziomie znajdują się taski, które nie wiedzą nic o agentach ani użytkowniku – realizują one proste operacje na dokumentach:

- **Pobieranie plików z mocka (już istnieje):**
  - `documents.tasks.fetch_and_store_file_task(document_id)` – używa `MockErpMesClient` z `erp_mes`, pobiera plik z mocka i zapisuje go w `Document.file`.

- **Parsowanie dokumentów (wstępny placeholder):**
  - `documents.tasks.parse_document_task(document_id)` – obecnie tylko loguje wywołanie, docelowo:
    - odczytuje plik z `Document.file`,
    - wyciąga tekst (dla PDF, JSON itp.),
    - dzieli na chunki,
    - zapisuje `DocumentChunk` oraz embeddingi.

Te taski stanowią „silnik techniczny” przetwarzania dokumentów.

### 4.2. Warstwa średniego poziomu – pipeline dokumentowy

Kolejny poziom to taski, które tworzą pipeline przetwarzania dokumentu lub zestawu dokumentów, np.:

- `build_document_index_task(document_id)`:
  - wywołuje sekwencyjnie:
    - `fetch_and_store_file_task` (jeśli dokument pochodzi z mocka i nie ma jeszcze pliku),
    - `parse_document_task` (ekstrakcja tekstu i embeddingów).

- `build_index_for_snapshot_task(stream, version_date)`:
  - pobiera listę dokumentów powiązanych z danym snapshotem (np. wszystkie `Document` z `mock_stream=erp`, `mock_version_date=...`),
  - dla każdego dokumentu wywołuje `build_document_index_task(document_id)` jako osobne zadanie lub grupę zadań.

Te taski można łączyć z Celery chains/groups, aby równolegle indeksować wiele dokumentów.

### 4.3. Warstwa wysokiego poziomu – zadania agentów

Na najwyższym poziomie znajdują się taski, które:

- przyjmują pytanie od użytkownika,
- decydują, które dokumenty / chunki są potrzebne,
- komunikują się z zewnętrznym API modeli językowych,
- zapisują wynik (streszczenie, quiz, odpowiedź).

Przykłady:

- `generate_summary_for_document_task(document_id, params)`:
  - zakłada, że dla dokumentu istnieje już indeks (chunki + embeddingi),
  - wybiera najważniejsze fragmenty (np. przez wektorowe wyszukiwanie w pgvector),
  - wywołuje zewnętrzne API (np. OpenAI) z kontekstem i prośbą o streszczenie,
  - zapisuje wynik w `SummaryArtifact`.

- `generate_quiz_for_document_task(document_id, params)`:
  - podobnie jak powyżej, ale prompt generuje pytania MCQ/SCQ,
  - wynik zapisuje w `QuizArtifact`.

- `answer_question_task(question, context_params)`:
  - na podstawie parametrów (np. które snapshoty, które dokumenty) wybiera potencjalnie istotne dokumenty,
  - wykonuje wektorowe wyszukiwanie chunków,
  - wywołuje zewnętrzne API z pytaniem i zebranym kontekstem,
  - zwraca odpowiedź oraz listę fragmentów, które zostały użyte (do pokazania użytkownikowi).

Zadania na tym poziomie muszą być świadome ograniczeń zewnętrznego API (limity tokenów, czasu odpowiedzi, kosztów) i odpowiednio dobierać rozmiar kontekstu oraz strategię chunkowania.

---

## 5. Integracja z zewnętrznym API modeli językowych

### 5.1. Klient do API modeli

Zaleca się wydzielenie klienta HTTP do API modeli językowych (np. OpenAI) do osobnego modułu, np. `ai_agents/llm_client.py`:

- odpowiedzialność:
  - przechowywanie kluczy i adresów endpointów w konfiguracji (zmienne środowiskowe),
  - obsługa retry (ograniczona liczba prób, backoff),
  - logowanie zapytań i odpowiedzi (bez wrażliwych danych),
  - mapowanie parametrów (temperature, top_p, max_tokens) na odpowiednie pola API,
  - opcjonalna obsługa trybu „assistants” (tworzenie wątków, wiadomości, plików).

Dzięki temu taski Celery nie muszą znać szczegółów protokołu zewnętrznego API; korzystają z prostych metod, np.:

```python
response = llm_client.generate_summary(context_chunks, instructions)
```

### 5.2. Bezpieczeństwo i separacja

- Klucze API są przechowywane w `.env` i przekazywane do kontenerów jako zmienne środowiskowe.
- Endpointy do agentów AI (np. „poproś o streszczenie”) powinny być chronione JWT i ewentualnie dodatkowymi rolami.
- Sensowne jest limitowanie liczby wywołań na użytkownika / na godzinę (rate limiting) oraz logowanie użycia (np. do przyszłej analizy kosztów).

---

## 6. Przykładowy pipeline „end-to-end”

Poniżej przykład, jak może wyglądać pełny przepływ od danych mock ERP/MES, przez dokumenty i agentów, aż do odpowiedzi dla użytkownika.

### 6.1. Etap 1 – synchronizacja ERP/MES i dokumentów

1. Celery Beat wywołuje cyklicznie `sync_erp_mes_snapshots_task` w `erp_mes`.
2. Task pobiera `manifest.json` z mock ERP/MES, aktualizuje `ErpMesSnapshot` i zapisuje listy plików (`files`).
3. Na podstawie snapshotu (np. wybranego w panelu admina lub przez osobne zadanie) tworzona jest seria `Document` dla wybranych plików ERP/MES przez endpoint `POST /api/documents/from-erp-mes/` lub osobne zadanie.
4. Dla dokumentów powiązanych z ERP/MES wywoływany jest pipeline indeksowania, np. `build_index_for_snapshot_task("erp", "2025-12-15")`, który uruchamia:
   - `fetch_and_store_file_task(document_id)` – pobranie fizycznych plików z mocka,
   - `parse_document_task(document_id)` – ekstrakcja tekstu, chunkowanie, embeddingi.

Rezultat: system ma w bazie `Document` + powiązane `DocumentChunk` (lub inny model indeksu) gotowy do użycia w RAG.

### 6.2. Etap 2 – interakcja użytkownika (pytanie lub prośba o streszczenie)

**Przykład A: Streszczenie dokumentu technicznego**

1. Użytkownik w UI wybiera dokument (np. specyfikacja PDF z mock docs) i wybiera akcję „wygeneruj streszczenie”.
2. Frontend wywołuje endpoint backendu, np. `POST /api/agents/summary/` z `document_id` i parametrami (poziom szczegółowości).
3. Backend tworzy `AgentJob` typu „summary” i uruchamia task Celery `generate_summary_for_document_task(document_id, params)`.
4. Task:
   - zapewnia, że dokument ma indeks (w razie potrzeby uruchamia pipeline indeksowania),
   - pobiera istotne chunki (np. całość albo podzbiór),
   - składa kontekst i instrukcje,
   - wywołuje `llm_client.generate_summary(...)`,
   - zapisuje wynik w `SummaryArtifact` i aktualizuje status `AgentJob`.
5. Frontend okresowo sprawdza status `AgentJob` (np. `GET /api/agents/jobs/<id>/`), a po zakończeniu pobiera streszczenie (`GET /api/agents/summary/<id>/`).

**Przykład B: Pytanie o aktualny stan systemu (RAG)**

1. Użytkownik zadaje pytanie dotyczące np. stanu produkcji na podstawie ostatniego snapshotu MES.
2. Frontend wywołuje `POST /api/agents/qa/` z treścią pytania i parametrami (np. „użyj najnowszego snapshotu MES”).
3. Backend tworzy `AgentJob` typu „qa” i uruchamia `answer_question_task(question, context_params)`.
4. Task:
   - identyfikuje właściwe dokumenty (np. wszystkie `Document` z `source=MOCK_MES`, `mock_version_date = latest`),
   - w oparciu o embeddingi wyszukuje najbardziej pasujące chunki,
   - buduje prompt z pytaniem i wybranym kontekstem,
   - wywołuje zewnętrzne API LLM,
   - zapisuje odpowiedź oraz listę wykorzystanych chunków (do wyświetlenia powiązań w UI).
5. Frontend pobiera odpowiedź i wyświetla użytkownikowi wraz z referencjami (np. linkami do dokumentów/sekcji).

### 6.3. Etap 3 – testy wiedzy (quizy)

1. Użytkownik wskazuje dokument lub zestaw dokumentów i wybiera akcję „wygeneruj quiz”.
2. Backend uruchamia `generate_quiz_for_document_task(document_id, params)`.
3. Task korzysta z tych samych chunków i embeddingów, ale prompt nakierowany jest na generowanie pytań (MCQ/SCQ) zamiast streszczenia.
4. Powstały `QuizArtifact` może zawierać listę pytań/odpowiedzi, gotowych do wyświetlenia w UI lub eksportu.

---

## 7. Kolejność prac wdrożeniowych

Proponowana kolejność implementacji po stronie agentów:

1. **Rozszerzenie `parse_document_task`**:
   - obsługa PDF i JSON,
   - ekstrakcja tekstu,
   - zapis chunków w bazie,
   - integracja z pgvector (embeddingi).

2. **Stworzenie modeli artefaktów (Summary, Quiz, ewentualnie AgentJob)**.

3. **Implementacja prostego clienta LLM (`llm_client`)**:
   - skonfigurowanie połączenia z zewnętrznym API (np. OpenAI),
   - implementacja funkcji `generate_summary`, `generate_quiz`, `answer_question`.

4. **Taski wysokiego poziomu dla agentów**:
   - `generate_summary_for_document_task`,
   - `generate_quiz_for_document_task`,
   - `answer_question_task`.

5. **Endpointy REST dla agentów i UI**:
   - tworzenie zadań agentów (POST),
   - odczyt artefaktów i statusów (GET).

6. **Optymalizacje i obserwowalność**:
   - retry i backoff dla połączeń z LLM,
   - lepsze logowanie (w tym powiązanie z `AgentJob`),
   - ewentualne rate limiting i podstawowa analityka użycia.

---

## 8. Podsumowanie

Istniejąca architektura backendu (moduły `erp_mes`, `documents`, Celery + Redis) tworzy solidne podstawy do budowy agentów AI:

- dane techniczne i operacyjne są dostępne jako snapshoty ERP/MES,
- dokumenty są reprezentowane w jednolity sposób i mają fizyczne pliki w `MEDIA_ROOT`,
- zadania Celery umożliwiają pobieranie i wstępne przetwarzanie dokumentów,
- wprowadzenie modułu agentów (np. `ai_agents`) pozwoli na warstwę:
  - parsowania i indeksowania (RAG),
  - komunikacji z LLM (OpenAI itp.),
  - generowania streszczeń, quizów i odpowiedzi na pytania użytkownika.

Dalsza praca polega na stopniowym uzupełnianiu pipeline’ów Celery o kolejne taski i modele artefaktów, tak aby cała logika agentów była wyraźnie oddzielona, dobrze obserwowalna i łatwa do rozwijania w kolejnych iteracjach projektu.
