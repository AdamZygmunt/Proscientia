# Dokumentacja Techniczna: Moduł Agenta AI (MVP)

**Temat:** Wdrożenie Agenta AI do streszczania dokumentów PDF  
**Data:** 26.11.2025  
**Status:** Wdrożono (MVP)

## 1. Cel Wdrożenia

Implementacja funkcjonalności umożliwiającej automatyczne generowanie streszczeń dokumentów technicznych (PDF) przechowywanych w systemie, przy wykorzystaniu modelu językowego OpenAI (GPT-4o).

---

## 2. Zmiany w Architekturze Systemu

### 2.1. Nowa Aplikacja Backendowa

Utworzono nowy moduł Django o nazwie **`ai_agents`** (`backend/ai_agents/`), który separuje logikę sztucznej inteligencji od reszty systemu.

### 2.2. Zmiany w Bazie Danych (PostgreSQL)

W wyniku migracji (`0001_initial.py`) w bazie danych utworzono nową tabelę fizyczną:

* **Nazwa tabeli:** `ai_agents_aisummary`
* **Struktura:**
    * `id` (Primary Key)
    * `document_id` (Foreign Key -> `documents_document`): Relacja 1:1 łącząca streszczenie z plikiem źródłowym.
    * `summary_text` (Text): Treść wygenerowanego streszczenia.
    * `created_at` (Timestamp): Data i czas wygenerowania.
* **Cel:** Trwałe przechowywanie wyników pracy agenta, co pozwala na ich wyświetlanie bez konieczności ponownego (płatnego) odpytywania API OpenAI.

---

## 3. Implementacja Logiki (Backend)

### 3.1. Modele Danych (`backend/ai_agents/models.py`)
Zdefiniowano model `AiSummary`, który mapuje się na tabelę w bazie danych. Model posiada relację `OneToOne` z modelem `Document`.

### 3.2. Serwis Logiczny (`backend/ai_agents/services.py`)
Stworzono logikę biznesową w funkcji `run_agent_summary`. Główne zadania serwisu:
1.  **Ekstrakcja:** Odczyt pliku PDF z dysku przy użyciu biblioteki `pypdf`.
    * *Optymalizacja:* W wersji MVP czytane jest maksymalnie 5 pierwszych stron dokumentu, aby zredukować koszty tokenów.
2.  **Przetwarzanie:** Tekst jest przycinany do bezpiecznego limitu znaków.
3.  **Interakcja z AI:** Wysłanie tekstu do OpenAI API (model `gpt-4o-mini`) z odpowiednim promptem systemowym ("Jesteś inżynierem...").

### 3.3. API REST (`backend/ai_agents/views.py`)
Wystawiono endpoint umożliwiający wywołanie agenta na żądanie:
* **URL:** `POST /api/agents/summarize/<doc_id>/`
* **Działanie:** Endpoint uruchamia proces w trybie synchronicznym (użytkownik czeka na odpowiedź), tworzy rekord w bazie i zwraca JSON z treścią streszczenia.

## 4. Zmiany w Infrastrukturze i Konfiguracji

Aby uruchomić agenta i ustabilizować środowisko Docker, wprowadzono szereg krytycznych poprawek w plikach konfiguracyjnych (`docker/` oraz `backend/`).

### 4.1. Naprawa Błędów Startowych (`docker/.env`)
* **Problem:** Kontener backendu nie uruchamiał się (`variable is not set`), ponieważ Docker Compose błędnie interpretował znaki `$` w `SECRET_KEY` jako zmienne.
* **Rozwiązanie:** Zmieniono format zmiennej `SECRET_KEY`, podwajając znaki dolara (`$$`).
* **Nowe zmienne:** Dodano klucze `OPENAI_API_KEY` oraz `OPENAI_MODEL_NAME`.

### 4.2. Naprawa Skryptu Startowego (`entrypoint.sh`)
* **Zmiana:** Przekonwertowano końce linii w pliku `docker/backend/entrypoint.sh` z formatu Windows (`CRLF`) na Unix (`LF`).
* **Cel:** Wyeliminowanie błędu `env: ‘bash\r’: No such file or directory`, który uniemożliwiał start kontenera na systemach Windows.

### 4.3. Obejście Blokady Frontendu (`docker/frontend/Dockerfile`)
* **Zmiana:** Zastąpiono restrykcyjną komendę `RUN npm ci` komendą `RUN npm install`.
* **Cel:** Umożliwienie budowania kontenera mimo niespójności między `package.json` a `package-lock.json` (brakujące zależności w pliku lock), co wcześniej blokowało start całego stacku.

### 4.4. Nowe Zależności (`backend/requirements.txt`)
Do projektu dodano biblioteki Python wymagane przez agenta:
* `openai` – klient API LLM.
* `pypdf` – obsługa plików PDF.
* `tiktoken` – narzędzie pomocnicze do tokenizacji.

## 5. Instrukcja Uruchomienia i Weryfikacji

### Krok 1: Przebudowa środowiska
Ze względu na zmiany w plikach `Dockerfile` i `requirements.txt`, wymagane jest przebudowanie kontenerów:

bash
cd docker
docker compose down
docker compose up -d --build

### Krok 2: Panel Administratora
Zarejestrowano nowe modele w plikach admin.py zarówno dla aplikacji documents, jak i ai_agents. Dzięki temu w panelu Django Admin (/admin/) dostępne są teraz:

Documents: Widok listy wgranych plików PDF.

Ai summaries: Widok listy wygenerowanych streszczeń z możliwością podglądu treści oraz daty utworzenia.

### Krok 3: Testowanie działania
Testy przeprowadzono pomyślnie przy użyciu Django Shell oraz bezpośrednich zapytań curl, potwierdzając, że system poprawnie odczytuje pliki z wolumenu, komunikuje się z OpenAI i zapisuje wyniki w bazie PostgreSQL.

![Streszczenie testowe agenta](Pierwsze_streszczenie.png)