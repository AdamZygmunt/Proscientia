Wdrożenie Agenta Wiedzy (QA / Chat z Dokumentem)
Data: 19.01.2026 Status: Zakończono pomyślnie ✅

1. Cel Wdrożenia
Celem dzisiejszych prac było uruchomienie funkcjonalności RAG (Retrieval-Augmented Generation) w interfejsie użytkownika. Umożliwia ona prowadzenie interaktywnego czatu z wybranym dokumentem, gdzie AI odpowiada na pytania wyłącznie na podstawie treści tego dokumentu (z podaniem źródeł).

2. Architektura Rozwiązania
System działa w modelu "Hybrydowym":

Backend (Django + pgvector): Odpowiada za logikę wyszukiwania semantycznego (szukanie fragmentów tekstu pasujących do pytania).

Frontend (React): Odpowiada za interfejs czatu (okno modalne) i komunikację z API.

🏢 Backend (Zmiany)
Nowy Endpoint: POST /api/agents/ask/<doc_id>/

Przyjmuje JSON: {"question": "..."}.

Zwraca JSON: {"answer": "...", "sources": ["...", "..."]}.

Logika (AskDocumentView w views.py):

Krok 1: Zamiana pytania użytkownika na wektor (Embedding) przy użyciu OpenAI (text-embedding-3-small).

Krok 2: Przeszukanie bazy danych (DocumentChunk) w celu znalezienia 5 fragmentów o najmniejszym dystansie euklidesowym (L2) od wektora pytania.

Krok 3: Sklejenie fragmentów w "Kontekst".

Krok 4: Wysłanie do GPT-4o-mini promptu systemowego: "Odpowiadaj tylko na podstawie poniższego kontekstu".

Routing (urls.py):

Zarejestrowano nową ścieżkę dla widoku QA.

🖥️ Frontend (Zmiany)
Nowy Komponent: DocumentChatModal.tsx

Niezależne okno dialogowe (Modal) wyświetlane nad aplikacją.

Obsługuje historię czatu (User vs Assistant).

Wyświetla źródła (cytaty), na których oparło się AI, co zwiększa wiarygodność odpowiedzi.

Wykorzystuje "czysty" React (useState, useRef) bez zewnętrznych bibliotek czatowych.

Integracja w AISummary.tsx

Dodano przycisk "Zapytaj" na kafelkach dokumentów (obok przycisku "Streszczaj").

Kliknięcie otwiera modal w kontekście konkretnego dokumentu.

3. Przepływ Danych (Data Flow)
Kiedy użytkownik zadaje pytanie:

Frontend wysyła tekst pytania do API.

Backend nie czyta całego pliku (co byłoby wolne i drogie).

Backend przeszukuje tabelę DocumentChunk (gdzie wcześniej pocięliśmy plik na kawałki po ~1000 znaków).

Znalezione "chunki" są wstrzykiwane do promptu GPT.

GPT generuje odpowiedź.

Użytkownik otrzymuje odpowiedź w ułamku sekundy (dzięki szybkiemu wyszukiwaniu wektorowemu).

4. Wymagania Wstępne (Ważne!)
Aby czat działał dla danego dokumentu, musi on zostać wcześniej zindeksowany.

Proces indeksowania (cięcie na chunki + embedding) uruchamia się endpointem /api/agents/index/<id>/.

Jeśli dokument nie jest zindeksowany, Czat zwróci komunikat o błędzie.

5. Pliki Zmodyfikowane/Dodane
backend/ai_agents/views.py (Logika RAG)

backend/ai_agents/urls.py (Routing)

frontend/src/components/DocumentChatModal.tsx (Nowy komponent UI)

frontend/src/pages/AISummary.tsx (Integracja przycisku)