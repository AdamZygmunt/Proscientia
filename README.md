<img src="./frontend/src/assets/logo-transparent-white.png" alt="Logo" style="width:30%;" />

## 👥 Autorzy
**Greń Piotr**

**Zygmunt Adam**

## 📚 Spis treści
1. [Architektura](#architektura)
2. [Setup – uruchomienie projektu](#setup--uruchomienie-projektu)

---

## 1. Architektura

Struktura katalogu głównego projektu:

```
proscientia/
├─ backend/          # Django REST Framework (API)
├─ frontend/         # React + Vite + TypeScript + TailwindCSS (UI)
├─ mock/             # FastAPI – symulacja systemów ERP/MES
├─ docker/
│  ├─ backend/       # Dockerfile + entrypoint dla backendu
│  ├─ frontend/      # Dockerfile dla frontendu
│  ├─ mock/          # Dockerfile + entrypoint dla mock API
│  ├─ celery/        # Dockerfile + entrypoint dla Celery/Beat
│  ├─ postgres/      # Dockerfile dla bazy danych PostgreSQL
│  ├─ compose.yaml   # Główny plik uruchamiający stack
│  └─ .env           # Zmiennie środowiskowe (konfiguracja projektu)
├─ data/
│  ├─ postgres/      # Wolumen bazy danych
│  ├─ pgadmin/       # Dane narzędzia pgAdmin
│  └─ media/         # Pliki użytkownika i cache dokumentów
└─ README.md
```

### Opis najważniejszych katalogów
1. **backend/** – aplikacja Django REST Framework. Obsługuje API, logikę serwera, dostęp do bazy danych oraz integrację z Celery.
2. **frontend/** – aplikacja React + Vite z TailwindCSS. Warstwa wizualna i interfejs użytkownika.
3. **mock/** – mikroserwis FastAPI udający zewnętrzne systemy ERP/MES. Posiada endpointy `/erp`, `/mes`, `/files` oraz `/health`.
4. **docker/** – pliki Dockerfile, skrypty startowe (`entrypoint.sh`) i główny `compose.yaml`, który spina wszystkie serwisy.
5. **data/** – lokalne wolumeny (persistencja danych Postgresa, pgAdmina i mediów).
6. **README.md** – bieżący plik dokumentacji.

---

## 2. Setup – uruchomienie projektu

Poniższe kroki pozwolą Ci uruchomić lokalnie cały stack aplikacji **Proscientia** na Twoim komputerze.

### 🔹 Krok 1. Klonowanie repozytorium

Upewnij się, że masz zainstalowanego **Git** oraz **Docker Desktop** (lub Docker Engine + Compose).  
Następnie sklonuj projekt:

```bash
git clone https://github.com/PiotrGren/Proscientia.git
cd proscientia/docker
```

### 🔹 Krok 2. Przygotowanie środowiska

Skopiuj plik `.env.example` (jeśli istnieje) lub utwórz `.env` według poniższego wzoru:

```
# --- DB ---
DB_NAME=dbname
DB_USER=dbadmin
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432

# --- Frontend ---
VITE_API_URL=http://backend:8000

# --- Backend ---
SECRET_KEY="change-me"
DEBUG=1
ALLOWED_HOSTS=*,localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
TIME_ZONE=Europe/Warsaw
MOCK_API_BASE=http://mock-erp-mes:8001

# --- Mock ---
MOCK_DATA_ROOT=/data
MOCK_MANIFEST_PATH=/data/manifest.json

# --- Redis / Celery ---
REDIS_URL=redis://redis:6379/0
# ROLE=worker  # albo beat
DJANGO_SETTINGS_MODULE=config.settings.dev

# --- pgAdmin ---
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=password
```

### 🔹 Krok 3. Budowanie obrazów Dockera

Z poziomu katalogu `docker/` wykonaj:

```bash
docker compose -f compose.yaml --env-file .env build --no-cache
```

### 🔹 Krok 4. Uruchomienie stacka

Po zakończonym buildzie uruchom kontenery:

```bash
docker compose -f compose.yaml --env-file .env up
```

Docker utworzy i uruchomi wszystkie kontenery: **frontend**, **backend**, **mock-erp-mes**, **db**, **pgadmin**.

### 🔹 Krok 5. Sprawdzenie działania

- **Frontend:** [http://localhost:5173](http://localhost:5173)  
  Zobaczysz placeholderową stronę React z napisem „Proscientia — Frontend działa 🚀”.
- **Backend:** [http://localhost:8000/admin](http://localhost:8000/admin)  
  Panel Django (po zalogowaniu superuserem). Na razie czysty szkielet API.
- **Mock API:** [http://localhost:8001/health](http://localhost:8001/health)  
  Endpoint zdrowia FastAPI – powinien zwrócić `{"status":"ok"}`.
- **pgAdmin:** [http://localhost:5050](http://localhost:5050)  
  Zaloguj się danymi z `.env`, następnie dodaj serwer `db` (host: `db`, port: `5432`).

### 🔹 Krok 6. Zatrzymanie kontenerów

Aby zatrzymać działające serwisy, naciśnij **Ctrl+C**, a następnie usuń kontenery:

```bash
docker compose -f compose.yaml down
```

---

> ✅ Po wykonaniu tych kroków masz gotowe środowisko deweloperskie Proscientia — z działającym frontendem, backendem, bazą danych i mock API.  
> W kolejnym etapie rozwijane będą funkcjonalności Django, React oraz integracje z agentami AI.
