# Integracja Silnika RAG z Systemem Artefaktów (Hybrid Engine)

Ten dokument opisuje zmiany wprowadzone w celu zintegrowania **Silnika Wektorowego (RAG)** z wersją aplikacji opartą na **Artefaktach i Frontendzie**.

Celem integracji było zachowanie warstwy wizualnej i logiki biznesowej (limity, zarządzanie plikami) przy jednoczesnym dodaniu "mózgu" (bazy wektorowej), który umożliwia inteligentne przeszukiwanie treści, a nie tylko proste streszczanie.

## 1. Wprowadzone Zmiany (Backend & Infrastruktura)

Poniższa lista opisuje pliki, które zostały zmodyfikowane lub dodane względem oryginalnej wersji repozytorium (branch `dev`).

### 🏗️ Infrastruktura i Konfiguracja

* **`docker/compose.yaml`**
    * **Zmiana:** Podmiana obrazu bazy danych z domyślnego `postgres` na `pgvector/pgvector:pg16`.
    * **Cel:** Umożliwienie przechowywania wektorów (embeddings) w bazie danych PostgreSQL.
* **`backend/requirements.txt`**
    * **Zmiana:** Dodanie bibliotek `pgvector` oraz `langchain-text-splitters`.
    * **Cel:** Obsługa operacji wektorowych w Django oraz inteligentne dzielenie tekstu na fragmenty (smart chunking).
* **Skrypty startowe (`entrypoint.sh` dla Backend/Celery)**
    * **Naprawa:** Zmiana kodowania końców linii z Windows (`CRLF`) na Unix (`LF`). Edytowano także plik .gitattributes by tego automatycznie nie zamieniał
    * **Cel:** Rozwiązanie błędu `env: ‘bash\r’: No such file or directory`, uniemożliwiającego start kontenerów na systemach Windows.

### 🧠 Logika AI (Aplikacja `ai_agents`)

* **`backend/ai_agents/models.py`**
    * **Zmiana:** Dodanie modelu **`DocumentChunk`** obok istniejącego modelu `AiArtifact`.
    * **Cel:** `AiArtifact` przechowuje pliki wynikowe (np. PDF z raportem), natomiast `DocumentChunk` przechowuje "wiedzę" (fragmenty tekstu i ich wektory) służącą do wyszukiwania semantycznego.
* **`backend/ai_agents/services.py`**
    * **Zmiana:** Dodanie funkcji `create_smart_chunks` (używa LangChain) oraz `get_embedding` (używa OpenAI API).
    * **Cel:** Zastąpienie prostego mechanizmu cięcia tekstu zaawansowanym pipeline'em RAG (zachowanie kontekstu zdań).
* **`backend/ai_agents/tasks.py`**
    * **Zmiana:** Implementacja taska Celery `process_document_indexing_task`.
    * **Cel:** Asynchroniczne przetwarzanie dokumentu: Pobranie -> Podział na chunki -> Embedding -> Zapis w DB.
* **`backend/ai_agents/admin.py`**
    * **Zmiana:** Rejestracja modelu `DocumentChunk`.
    * **Cel:** Możliwość podglądu zindeksowanych fragmentów w Panelu Administratora Django.

### 🔌 API i Widoki

* **`backend/ai_agents/views.py`**
    * **Zmiana:** Dodanie widoku `TriggerIndexingView` (oraz przygotowanie pod `AskDocumentView`).
    * **Cel:** Endpoint umożliwiający ręczne uruchomienie procesu indeksowania dla danego dokumentu.
* **`backend/ai_agents/urls.py`**
    * **Zmiana:** Rejestracja ścieżki `/api/agents/index/<doc_id>/` (oraz `/ask/`).

---

## 2. Status Obecny

System posiada teraz **dwa niezależne tryby pracy** z dokumentem:

1.  **Tryb Artefaktu (Legacy):** Generuje fizyczny plik (np. streszczenie `.txt`) i zapisuje go w historii. Używa prostego mechanizmu cięcia tekstu.
2.  **Tryb Wiedzy / RAG (New):** Rozbija dokument na setki wektorów i zapisuje w tabeli `DocumentChunk`. Nie generuje pliku dla użytkownika, ale buduje indeks pod przyszłe pytania (Semantic Search).

**Weryfikacja działania:**
* Wysłanie `POST` na `/api/agents/index/<id>/` uruchamia proces.
* Logi Celery potwierdzają operację komunikatem: `Indexed X chunks`.
* W panelu Admina (`/admin/`) widać fragmenty w sekcji `Document chunks`.

---

## 3. Plan Wdrożenia: Agent Asystent Wiedzy (QA)

Kolejnym krokiem jest wykorzystanie zbudowanego indeksu do stworzenia Agenta, który odpowiada na pytania (Chat z dokumentem).

### Krok A: Backend - Endpoint Wyszukiwania
* **Logika:**
    1.  Odbierz pytanie od użytkownika (JSON: `{"question": "..."}`).
    2.  Zamień pytanie na wektor (Embedding).
    3.  Wykonaj **Semantic Search** w tabeli `DocumentChunk` (znajdź 3-5 fragmentów najbliższych tematycznie).
    4.  Sklej fragmenty w `Context`.
    5.  Wyślij do GPT prompt: *"Odpowiedz na pytanie używając TYLKO poniższego kontekstu"*.

### Krok B: Frontend - Interfejs QA
* **UI:** Dodanie przycisku "Zadaj pytanie" lub okna czatu obok dokumentu na liście.
* **Logika:**
    1.  Sprawdzenie, czy dokument jest zindeksowany.
    2.  Jeśli tak -> Pokaż input na pytanie i wyświetl odpowiedź z API.
