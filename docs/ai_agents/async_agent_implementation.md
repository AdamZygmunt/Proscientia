# Dokumentacja Wdrożenia: Asynchroniczny Agent AI i WebSockets

**Data:** 10.12.2025
**Autor:** Adam Zygmunt
**Status:** Backend Ready / Frontend Pending

## 1. Cel Zmian
Celem tej sesji było przekształcenie synchronicznego agenta AI (blokującego żądanie HTTP) w rozwiązanie asynchroniczne oparte o **Celery** oraz przygotowanie infrastruktury **WebSockets (Django Channels)** do powiadamiania frontendu o postępie prac w czasie rzeczywistym.

## 2. Kluczowe Zmiany Architektoniczne

### 2.1. Przejście na ASGI (Asynchronous Server Gateway Interface)
* Zmieniono serwer aplikacyjny z WSGI na **ASGI**, aby umożliwić obsługę WebSockets.
* Wdrożono serwer **Daphne** jako główny serwer dla Django w kontenerze Dockera.
* Skonfigurowano `CHANNEL_LAYERS` z wykorzystaniem **Redis** jako backendu komunikacyjnego.

### 2.2. Asynchroniczne Przetwarzanie (Celery)
* **Widok API (`TriggerSummaryView`)**: Zamiast generować streszczenie natychmiast, endpoint teraz jedynie zleca zadanie i zwraca `task_id`.
* **Task Celery (`generate_summary_task`)**: Logika agenta (OpenAI) została przeniesiona do workera Celery. Task ten po zakończeniu pracy wysyła sygnał przez WebSockets.

### 2.3. Naprawa Infrastruktury Docker
Wprowadzono krytyczne poprawki, aby kontenery działały stabilnie na Windows i Linux:
* **Backend & Celery**: Naprawiono format końców linii (CRLF -> LF) w plikach `entrypoint.sh`, co powodowało błędy startu (`bash\r: No such file`).
* **Frontend**: Zmieniono `RUN npm ci` na `RUN npm install` w Dockerfile, aby umożliwić budowanie obrazu mimo niespójności w `package-lock.json`.
* **Zmienne Środowiskowe**: Poprawiono format `SECRET_KEY` w `.env` (escapowanie znaków `$`).

## 3. Szczegóły Implementacji

### Nowe Pliki i Moduły
* `backend/ai_agents/consumers.py`: Obsługa połączenia WebSocket (nasłuchiwanie w grupie `global_notifications`).
* `backend/ai_agents/routing.py`: Mapowanie URL `ws/notifications/`.
* `backend/ai_agents/tasks.py`: Zaktualizowany task, który używa `channel_layer` do wysyłania powiadomień o statusie (`started`, `completed`, `error`).

### Zaktualizowane Endpointy
**POST** `/api/agents/summarize/<doc_id>/`
* **Zachowanie**: Zleca task w tle.
* **Response (202 Accepted)**:
  
  {
      "message": "Zadanie przyjęte do realizacji.",
      "task_id": "216f2fd1-1754-4c45-9399-e577a1b8b8d9",
      "document_id": 1,
      "websocket_url": "/ws/notifications/"
  }
  
![Potwierdzenie wykonania w logach celery](./Logs_celery_api1.png)

### Kanał WebSocket
**URL:** ws://localhost:8000/ws/notifications/

Zdarzenia: Klient otrzymuje JSON z typem task_update i payloadem zawierającym status oraz wynik streszczenia.