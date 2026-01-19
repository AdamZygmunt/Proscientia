import os
import pypdf    # type: ignore
import json
from openai import OpenAI
from django.conf import settings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from documents.models import Document 
from .models import AiArtifact


def extract_text(file_path):
    """Wyciąga tekst z PDF. Czyta CAŁY plik (usunięto limit 5 stron)."""
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            # Usunięto if i >= 5: break
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Błąd PDF: {e}")
    return text

def run_agent_summary(document_path):
    """Wysyła tekst do OpenAI."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # 1. Pobierz tekst
    raw_text = extract_text(document_path)
    if not raw_text:
        return "Nie udało się odczytać tekstu z pliku."

    # 2. Skróć (bezpiecznik kosztowy)
    truncated_text = raw_text[:20000]

    # 3. Zapytanie do AI
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": "Jesteś inżynierem. Streszczaj dokumenty techniczne w punktach."},
                {"role": "user", "content": f"Dokument:\n{truncated_text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Błąd OpenAI: {str(e)}"
    

def _extract_text_pdf(file_path: str) -> str:
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)
        print(f"--- [DEBUG] Rozpoczynam czytanie PDF. Liczba stron: {total_pages} ---") # <--- SZPIEG 1
        
        for i, page in enumerate(reader.pages):
            # Upewnij się, że NIE MA TU IF BREAK
            page_text = page.extract_text() or ""
            text += page_text + "\n"
            print(f"--- [DEBUG] Przetworzono stronę {i+1}/{total_pages} (długość: {len(page_text)}) ---") # <--- SZPIEG 2
            
    except Exception as e:
        print(f"[AiAgents] Błąd PDF: {e}")
    return text


def _extract_text_plain(file_path: str, encoding: str = "utf-8") -> str:
    try:
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"[AiAgents] Błąd przy czytaniu pliku tekstowego: {e}")
        return ""


def _extract_text_json(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        # prosty pretty-print JSON-a jako tekst wejściowy
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AiAgents] Błąd przy czytaniu JSON: {e}")
        return ""


def _extract_text_jsonl(file_path: str) -> str:
    lines = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    lines.append(json.dumps(obj, ensure_ascii=False))
                except json.JSONDecodeError:
                    lines.append(line)
    except Exception as e:
        print(f"[AiAgents] Błąd przy czytaniu JSONL: {e}")
    return "\n".join(lines)


def _extract_text_generic(file_path: str) -> str:
    """
    Fallback dla formatów typu yaml/yml/xml/doc/docx – na razie czytamy je
    jako zwykły tekst. W przyszłości możemy tu podpiąć dedykowane parsery.
    """
    return _extract_text_plain(file_path)


def extract_text_from_document(document: Document) -> str:
    """
    Wyciąga tekst z Document w zależności od rozszerzenia / content_type.
    Tu NIE ma jeszcze logiki 'scope' – to tylko ekstrakcja całego pliku.
    """
    if not document.file:
        return ""

    file_path = document.file.path
    ext = os.path.splitext(file_path)[1].lower()
    content_type = (document.content_type or "").lower()

    # PDF
    if ext == ".pdf" or "pdf" in content_type:
        return _extract_text_pdf(file_path)

    # TXT
    if ext == ".txt" or content_type.startswith("text/"):
        return _extract_text_plain(file_path)

    # JSON / JSONL
    if ext == ".json":
        return _extract_text_json(file_path)
    if ext == ".jsonl":
        return _extract_text_jsonl(file_path)

    # YAML / YML / XML / DOC / DOCX – na razie traktujemy jako tekst
    if ext in {".yaml", ".yml", ".xml", ".doc", ".docx"}:
        return _extract_text_generic(file_path)

    # Fallback
    return _extract_text_generic(file_path)


def chunk_text(text: str, max_chars: int = 2000) -> list[str]:
    """
    Prosty chunking po znakach. W przyszłości możemy podmienić na
    'inteligentny' chunking po zdaniach/sekcjach.
    """
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end
    return chunks


def rerank_chunks(chunks: list[str], metadata: dict | None = None) -> list[str]:
    """
    Placeholder pod przyszły re-rank (np. na podstawie DocSearch).
    Na razie zwracamy wprost, ale interfejs już jest gotowy.
    """
    return chunks


def prepare_text_for_summary(
    document: Document,
    scope: dict | None = None,
    max_chars: int = 20000,
) -> tuple[str, dict]:
    """
    Buduje tekst wejściowy do streszczenia:
    - ekstrakcja z pliku,
    - prosty chunking,
    - opcjonalny re-rank (na razie placeholder),
    - przycięcie do max_chars.
    Zwraca (tekst, metadata).
    """
    raw_text = extract_text_from_document(document)
    if not raw_text:
        return "", {
            "scope": scope,
            "chunks": 0,
            "original_length": 0,
            "truncated_length": 0,
        }

    chunks = chunk_text(raw_text, max_chars=2000)
    chunks = rerank_chunks(chunks, metadata={"scope": scope})

    merged = "".join(chunks)
    truncated = merged[:max_chars]

    meta = {
        "scope": scope,
        "chunks": len(chunks),
        "original_length": len(raw_text),
        "truncated_length": len(truncated),
    }
    return truncated, meta


def run_agent_summary_from_text(
    text: str,
    scope: dict | None = None,
    system_prompt: str | None = None,
) -> tuple[str, dict]:
    """
    Ogólny helper: streszczenie z dowolnego tekstu.
    Używany przez:
      - run_agent_summary_for_document
      - raport ERP/MES (quick report)
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    if not text:
        return "Brak danych wejściowych do streszczenia.", {
            "scope": scope,
            "original_length": 0,
        }

    default_system = (
        "Jesteś inżynierem. Streszczaj dane i dokumenty techniczne "
        "w zwięzłych punktach, zrozumiałych dla inżyniera produkcji."
    )
    system_msg = system_prompt or default_system

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": f"Zakres: {scope}. Dane wejściowe:\n{text}",
                },
            ],
        )
        summary_text = response.choices[0].message.content or ""
        meta = {
            "scope": scope,
            "original_length": len(text),
        }
        return summary_text, meta
    except Exception as e:
        error_msg = f"Błąd OpenAI: {str(e)}"
        return error_msg, {
            "scope": scope,
            "original_length": len(text),
            "error": str(e),
        }


def run_agent_summary_for_document(
    document: Document,
    scope: dict | None = None,
) -> tuple[str, dict]:
    """
    Docelowa funkcja agenta streszczeń:
    - pracuje na obiekcie Document,
    - korzysta z prepare_text_for_summary (chunking, scope placeholder),
    - zwraca (summary_text, summary_metadata).
    """
    prepared_text, prep_meta = prepare_text_for_summary(document, scope=scope)
    if not prepared_text:
        msg = "Nie udało się odczytać tekstu z pliku."
        return msg, {"preparation": prep_meta}

    system_prompt = (
        "Jesteś inżynierem. Streszczaj dokumenty techniczne "
        "w punktach, zrozumiale dla inżyniera produkcji."
    )

    summary_text, llm_meta = run_agent_summary_from_text(
        prepared_text,
        scope=scope,
        system_prompt=system_prompt,
    )

    return summary_text, {
        "preparation": prep_meta,
        "llm": llm_meta,
    }




    
def count_user_summaries_for_document(user, document) -> int:
    """
    Liczba streszczeń (AiArtifact typu 'summary') dla danego dokumentu i użytkownika.
    Limit: max 3 na doc per user.
    """
    if user.is_anonymous:
        return 0

    return AiArtifact.objects.filter(
        owner=user,
        document=document,
        artifact_type=AiArtifact.TYPE_SUMMARY,
    ).count()


def build_summary_filename(document, user) -> str:
    """
    Nazwa pliku txt dla streszczenia.
    Użyjemy później w tasku Celery.
    """
    base = f"summary_doc{document.id}_user{user.id}"
    return f"{base}.txt"

# RAG / EMBEDDINGS UTILS (DODANE)

def create_smart_chunks(text, chunk_size=1000, chunk_overlap=200):
    """
    Używa LangChain do mądrego dzielenia tekstu (nie ucina zdań w połowie).
    Zastępuje prosty chunk_text Piotra w zastosowaniach RAG.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)

def get_embedding(text):
    """Zamienia tekst na wektor liczbowy (1536 liczb) używając OpenAI."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    text = text.replace("\n", " ")
    
    try:
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Błąd Embedding OpenAI: {e}")
        return []