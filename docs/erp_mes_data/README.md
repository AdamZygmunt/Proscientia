# Dokumentacja danych ERP/MES w serwisie mock

> **Lokalizacja:** `mock/data/`

Celem tego dokumentu jest wyjaśnienie **jakie dane przechowujemy w serwisie mock**, **jak są zorganizowane** oraz **jaką historię biznesową symulują**.  
Dokument jest pisany tak, aby był zrozumiały zarówno dla członków zespołu, jak i dla prowadzącego / recenzentów – bez konieczności zaglądania w kod.

---

## 1. Ogólna koncepcja danych w serwisie mock

Serwis `mock` udostępnia sztucznie wygenerowane, ale **spójne** dane, które:

- udają dane z systemów **ERP** (planowanie produkcji, zlecenia, BOM, maszyny, plany utrzymania),  
- udają dane z systemów **MES** (rzeczywisty przebieg produkcji, partie, jakość, przestoje, obsada zmian),  
- powiązane są z **dokumentami inżynierskimi** (instrukcje, wymagania, schematy, procedury jakości) zapisanymi w katalogu `docs/`,  
- tworzą **narrację w czasie** – od startu linii produkcyjnej respiratora PB560, przez problemy jakościowe, aż po działania korygujące i stabilną produkcję.

Dane mock są wykorzystywane przez:

- **backend** – do budowania modeli, endpointów i scenariuszy analitycznych,  
- **agenty AI / RAG** – jako źródło wiedzy o „świecie” fabryki, z którym użytkownik może rozmawiać w języku naturalnym.

---

## 2. Struktura katalogu `mock/data/`

Wewnątrz katalogu `mock/data/` znajdują się trzy główne obszary:

```bash
mock/
└─ data/
   ├─ erp/
   │  ├─ 2025-12-15/
   │  ├─ 2026-01-31/
   │  ├─ 2026-02-22/
   │  └─ 2026-03-30/
   ├─ mes/
   │  ├─ 2025-12-15/
   │  ├─ 2026-01-31/
   │  ├─ 2026-02-22/
   │  └─ 2026-03-30/
   ├─ docs/
   │  ├─ budownictwo/
   │  ├─ finance/
   │  ├─ safety/
   │  └── ventilator_pb560/
   └─ manifest.json
```

### 2.1. `mock/data/erp/`

- Zawiera **migawki danych ERP** (po jednej na folder z datą).
- Każdy folder daty (`YYYY-MM-DD`) reprezentuje **stan systemu ERP na daną datę**.
- Wewnątrz każdej daty znajdują się te same pliki (szczegóły w rozdziale 3).

### 2.2. `mock/data/mes/`

- Zawiera **migawki danych MES** – czyli rzeczywiste wykonanie produkcji, jakości, przestojów.
- Struktura jest analogiczna do `erp/` – foldery z datami i powtarzalny zestaw plików (opis w rozdziale 4).

### 2.3. `mock/data/docs/`

- Zawiera **surowe dokumenty inżynierskie**, m.in.:
  - dokumenty budowlane i BHP (`budownictwo/`, `safety/`),
  - dokumenty finansowe (`finance/`),
  - kluczowe dokumenty dla respiratora PB560 (`ventilator_pb560/`):
    - instrukcje użytkownika i serwisowe,
    - wymagania produktowe i programowe,
    - schematy elektryczne,
    - procedury jakości i testów.

Te dokumenty są używane jako **tło dla scenariusza** (np. RAG może tłumaczyć decyzje w danych ERP/MES, odwołując się do wymagań / procedur zapisanych w PDF-ach).

### 2.4. `mock/data/manifest.json`

Plik `manifest.json` jest centralnym indeksem wersji danych ERP/MES.

Przykład struktury (uproszczony):

```json
{
  "erp": {
    "latest": "2026-03-30",
    "versions": [
      "2025-12-15",
      "2026-01-31",
      "2026-02-22",
      "2026-03-30"
    ]
  },
  "mes": {
    "latest": "2026-03-30",
    "versions": [
      "2025-12-15",
      "2026-01-31",
      "2026-02-22",
      "2026-03-30"
    ]
  }
}
```

Interpretacja:

- `erp.latest` / `mes.latest` – domyślna wersja danych, którą powinien pobrać backend, jeżeli nie poda konkretnej daty.
- `erp.versions` / `mes.versions` – lista **wszystkich dostępnych migawek** (snapshots) danych.

API mock (FastAPI) będzie używać `manifest.json`, aby serwować:

- `/erp?version=YYYY-MM-DD` – dane ERP dla konkretnej daty,
- `/erp` bez parametru – dane ERP dla `latest`,
- `/mes?version=YYYY-MM-DD` oraz `/mes` dla MES,
- dodatkowo endpointy `/docs/...` serwujące pliki z katalogu `docs/`.

---

## 3. Dane ERP – pliki i ich znaczenie

W każdym katalogu `mock/data/erp/YYYY-MM-DD/` znajdują się te same pliki:

```bash
mock/data/erp/YYYY-MM-DD/
├─ work_orders.json
├─ bom.json
├─ routing.json
├─ machines.json
└─ maintenance_plans.json
```

### 3.1. `work_orders.json` – zlecenia produkcyjne

**Opis ogólny:**

Plik `work_orders.json` zawiera listę **zleceń produkcyjnych** (Work Orders, WO) na produkt PB560. Każde zlecenie opisuje:

- dla kogo produkujemy,
- ile sztuk,
- na której linii,
- w oparciu o którą wersję BOM i routingu,
- jaki jest status realizacji (planowane, w toku, zakończone, wstrzymane, anulowane).

**Typowe pola w rekordzie zlecenia:**

- `id` – unikalny identyfikator zlecenia, np. `"WO-2026-02-001"`.
- `product_id` – identyfikator produktu, tutaj `"PB560"`.
- `bom_version` – wersja BOM użyta do realizacji (np. `"v1"`, `"v2"`, `"v3"`).
- `routing_version` – wersja routingu (np. `"v1"`, `"v2"`).
- `customer` – odbiorca (np. szpital, rezerwa narodowa).
- `priority` – priorytet `"low" | "medium" | "high"`.
- `status` – `"planned" | "in_progress" | "completed" | "on_hold" | "cancelled"`.
- `quantity` – liczba sztuk do wyprodukowania.
- `quantity_completed` – liczba sztuk faktycznie ukończonych.
- `start_date`, `due_date` – planowane daty startu i zakończenia produkcji.
- `line_id` – identyfikator linii produkcyjnej (np. `"LINE-1"`, `"LINE-2"`).
- `created_at` – data utworzenia zlecenia.
- `closed_at` – data formalnego zamknięcia (dla zakończonych / anulowanych).
- `notes` – opis kontekstowy (np. „pierwszy pilotaż”, „po działaniach korygujących”).

### 3.2. `bom.json` – struktura materiałowa (Bill of Materials)

**Opis ogólny:**

Plik `bom.json` zawiera **wersjonowaną listę komponentów** dla produktu PB560. Każdy rekord opisuje jedną wersję BOM:

- które komponenty wchodzą w skład PB560,
- ile sztuk każdego komponentu jest zużywane na 1 produkt,
- od jakiego dostawcy pochodzi komponent,
- w jakim okresie dana wersja BOM była ważna.

**Typowe pola:**

- `product_id` – identyfikator produktu (`"PB560"`).
- `version` – wersja BOM (`"v1"`, `"v2"`, `"v3"`).
- `valid_from` – data, od której BOM jest obowiązujący.
- `valid_to` – (opcjonalnie) data końca obowiązywania (dla wersji zastąpionych nowszym BOM).
- `description` – opis słowny (np. „pilotowa wersja BOM”, „wersja problematyczna”, „wersja po działaniach korygujących”).
- `components` – lista komponentów, gdzie każdy element zawiera:
  - `component_id` – np. `"PB560-VALVE-SET"`,
  - `description` – opis komponentu,
  - `uom` – jednostka miary (`"pcs"`, `"set"`),
  - `quantity_per` – ile sztuk na jeden produkt,
  - `supplier` – nazwa dostawcy.

**Scenariusz zmian BOM:**

- `v1` – bazowy BOM dla pilotażu (dostawca zaworu A).
- `v2` – wersja z nowym, „tańszym” dostawcą zaworów – pojawiają się problemy jakościowe (MES).
- `v3` – wersja po działaniach korygujących – zmiana dostawcy / parametrów + zaostrzone kontrole wejściowe.

### 3.3. `routing.json` – proces technologiczny (routing)

**Opis ogólny:**

Plik `routing.json` opisuje **sekwencję operacji technologicznych**, które musi przejść produkt PB560 (np. montaż elektroniki, montaż mechaniczny, testy, pakowanie).

**Typowe pola w definicji routingu:**

- `product_id` – `"PB560"`.
- `version` – wersja routingu (`"v1"`, `"v2"`).
- `valid_from`, `valid_to` – zakres obowiązywania.
- `description` – opis, np. „routing bazowy”, „routing po dodaniu kroku kontroli przepływu”.
- `operations` – lista operacji, każda zawiera:
  - `operation_id` – np. `"OP-040"`.
  - `name` – nazwa operacji (np. „Electrical safety test”).
  - `sequence` – numer kolejności (10, 20, 30, …).
  - `workcenter_id` – id stanowiska/gniazda (np. `"WC-TEST-01"`).
  - `std_time_min` – czas standardowy na operację (w minutach).
  - `labor_skill` – wymagany typ operatora.
  - `is_critical` – czy operacja jest krytyczna dla jakości/safety.

**Scenariusz zmian routingu:**

- `v1` – podstawowy ciąg operacji.
- `v2` – dodany krok „Valve flow pre-check” przed testem funkcjonalnym, z nieco wydłużonym czasem testu – odzwierciedla działania korygujące po wykryciu problemów z zaworami.

### 3.4. `machines.json` – maszyny i stanowiska

**Opis ogólny:**

Plik `machines.json` opisuje dostępne **maszyny / stanowiska robocze** (workcenters) w fabryce:

- linie produkcyjne,
- stanowiska mechaniczne,
- stanowiska testowe,
- stanowiska pakowania.

**Typowe pola:**

- `machine_id` – np. `"WC-SMT-01"`, `"WC-TEST-02"`.
- `name` – nazwa czytelna dla człowieka.
- `type` – typ stanowiska (`"SMT"`, `"assembly_station"`, `"test_bench"`, `"inspection_station"`).
- `location` – lokalizacja fizyczna (np. hall, laboratorium).
- `line_id` – `"LINE-1"` lub `"LINE-2"` – przypisanie do linii.
- `status` – np. `"available"`.
- `commissioned_at` – data uruchomienia.
- `remarks` – komentarze (np. „główna linia SMT dla PB560”, „stanowisko do kontroli przepływu”).

### 3.5. `maintenance_plans.json` – plany utrzymania ruchu

**Opis ogólny:**

Plik `maintenance_plans.json` opisuje **planowane działania utrzymania ruchu** dla maszyn:

- przeglądy dzienne,
- przeglądy tygodniowe/miesięczne,
- specjalne kontrole (np. dodatkowe kontrole zaworów po wdrożeniu BOM v3).

**Typowe pola:**

- `plan_id` – unikalny identyfikator planu.
- `machine_id` – do której maszyny plan się odnosi.
- `description` – opis czynności (np. „dzienne czyszczenie podajników SMT”).
- `frequency` – `"daily" | "weekly" | "monthly" | "per_lot"` itd.
- `last_performed_date` – kiedy ostatnio wykonano plan.
- `next_due_date` – kiedy plan jest kolejny raz wymagany.
- `responsible_role` – rola odpowiedzialna (np. „maintenance_technician”, „quality_engineer”).

---

## 4. Dane MES – pliki i ich znaczenie

Analogicznie do ERP, w każdym katalogu `mock/data/mes/YYYY-MM-DD/` znajdują się te same pliki:

```bash
mock/data/mes/YYYY-MM-DD/
├─ production_batches.json
├─ quality_checks.json
├─ downtime_log.json
└─ shift_log.json
```

### 4.1. `production_batches.json` – partie produkcyjne

**Opis ogólny:**

Plik `production_batches.json` zawiera listę **partii produkcyjnych** (batches). Każda partia jest powiązana z:

- konkretnym zleceniem produkcyjnym (WO),
- konkretną linią,
- zadaną i faktyczną liczbą sztuk,
- liczbą sztuk dobrych (OK) i braków (NOK).

**Typowe pola:**

- `batch_id` – np. `"B-2026-03-002"`.
- `work_order_id` – powiązanie z `work_orders.json`.
- `product_id` – `"PB560"`.
- `line_id` – np. `"LINE-1"`, `"LINE-2"`.
- `quantity_planned` – planowana liczba sztuk.
- `quantity_good` – liczba sztuk OK.
- `quantity_reject` – liczba sztuk NOK.
- `start_time`, `end_time` – ramy czasowe produkcji partii.
- `status` – np. `"completed"`, `"in_progress"`.
- `remarks` – komentarze (np. „pierwszy pilotaż”, „partia po działaniach korygujących”).

### 4.2. `quality_checks.json` – wyniki kontroli jakości

**Opis ogólny:**

Plik `quality_checks.json` opisuje **konkretne punkty kontroli** (checkpoints) i ich wyniki, powiązane z partiami:

- wyniki testów elektrycznych i funkcjonalnych,
- defekty kosmetyczne (np. zarysowane obudowy),
- kluczowe kody defektów związane z zaworami.

**Typowe pola:**

- `check_id` – identyfikator kontroli.
- `batch_id` – identyfikator partii (`production_batches.json`).
- `product_id` – `"PB560"`.
- `checkpoint` – nazwa punktu kontroli (np. „Final functional test”, „Valve flow pre-check”).
- `result` – `"pass"` lub `"fail"`.
- `defect_code` – kod defektu (np. `"VALVE_FLOW_VARIATION"`, `"SCRATCH_HOUSING"`, `null`).
- `measured_values` – słownik z wartościami pomiarów (np. liczba jednostek dotkniętych defektem, procent odchyłki przepływu).
- `inspector_id` – id inspektora/operatora.
- `timestamp` – czas wykonania kontroli.
- `remarks` – komentarz opisowy.

**Kluczowy scenariusz jakości:**

- we wcześniejszych migawkach (BOM v2) pojawiają się defekty `VALVE_FLOW_VARIATION` przy testach funkcjonalnych,
- po zmianie na BOM v3 + routing v2 defekty przepływu znikają,
- zostają głównie drobne defekty kosmetyczne (np. zarysowania obudowy).

### 4.3. `downtime_log.json` – przestoje maszyn

**Opis ogólny:**

Plik `downtime_log.json` zawiera **rejestr przestojów** na maszynach:

- przestoje nieplanowane (awarie, regulacje, problemy z narzędziem),
- przestoje planowane (wdrożenie działań korygujących, kalibracje, prewencja).

**Typowe pola:**

- `event_id` – identyfikator zdarzenia.
- `machine_id` – identyfikator maszyny (`machines.json`).
- `line_id` – identyfikator linii.
- `start_time`, `end_time` – czas trwania przestoju.
- `duration_min` – czas trwania w minutach.
- `type` – `"planned"` lub `"unplanned"`.
- `reason_code` – skrócony kod przyczyny (np. `"FEEDER_JAM"`, `"CALIBRATION"`, `"RETEST_DUE_TO_DEFECT"`).
- `description` – opis słowny zdarzenia.
- `reported_by` – osoba/rola zgłaszająca.

### 4.4. `shift_log.json` – obsada zmian

**Opis ogólny:**

Plik `shift_log.json` opisuje **obsadę zmian** na liniach produkcyjnych:

- jaka zmiana (data, kod zmiany),
- na której linii,
- który supervisor,
- jacy operatorzy uczestniczyli w produkcji.

**Typowe pola:**

- `shift_id` – identyfikator zmiany.
- `date` – data zmiany.
- `shift_code` – kod zmiany (np. `"A"`).
- `line_id` – `"LINE-1"` lub `"LINE-2"`.
- `supervisor_id` – id przełożonego.
- `operator_ids` – lista operatorów (np. `"OP-001"`, `"OP-003"`).
- `notes` – informacja kontekstowa (np. „zmiana wdrożeniowa działań korygujących”, „referencyjna zmiana po stabilizacji”).

---

## 5. Scenariusze czasowe (snapshots) i zmiany między wersjami

Dane ERP/MES są zorganizowane w **cztery migawki czasowe**, zdefiniowane w `manifest.json`:

- `2025-12-15`
- `2026-01-31`
- `2026-02-22`
- `2026-03-30`

Każda migawka ma **ten sam zestaw plików** w `erp/` i `mes/`, ale **inne wartości**, tak aby opowiadać spójną historię.

### 5.1. Snapshot 1 – `2025-12-15`  
**Start pilotażu linii PB560**

- **ERP:**
  - BOM w wersji `v1` (bazowy zestaw komponentów).
  - Routing w wersji `v1` (podstawowy ciąg operacji).
  - Kilka pierwszych zleceń produkcyjnych (małe wolumeny, pilotaż).
  - Jedna linia produkcyjna (`LINE-1`), podstawowe maszyny i plany utrzymania.

- **MES:**
  - Pierwsze partie produkcyjne (mieszanka partii w pełni OK i z pojedynczymi brakami).
  - Nieliczne defekty jakości – głównie kosmetyczne lub kalibracyjne.
  - Kilka drobnych, nieplanowanych przestojów (np. zacięty feeder SMT).
  - Shift log pokazuje pierwsze zmiany pilotażowe.

### 5.2. Snapshot 2 – `2026-01-31`  
**Rampa produkcji i pojawienie się problemów jakościowych (BOM v2)**

- **ERP:**
  - Do systemu wchodzi BOM w wersji `v2` – zmieniony dostawca zaworów (`PB560-VALVE-SET`).
  - Wciąż routing `v1`, ale zwiększona liczba zleceń (większe wolumeny, nowe szpitale).
  - Pojawia się druga linia / stanowisko (`LINE-2`) dla zwiększenia przepustowości.

- **MES:**
  - Większe partie produkcyjne, w tym partie z **wyraźnie podniesionym odsetkiem braków**.
  - W `quality_checks.json` pojawiają się defekty `VALVE_FLOW_VARIATION` przy testach funkcjonalnych, powiązane z partiami produkowanymi na BOM `v2`.
  - W `downtime_log.json` pojawiają się przestoje związane z dodatkowymi retestami i regulacjami.
  - W `shift_log.json` można zobaczyć zmiany, w których następuje eskalacja problemów.

### 5.3. Snapshot 3 – `2026-02-22`  
**Działania korygujące: BOM v3 + routing v2**

- **ERP:**
  - Pojawia się BOM `v3` – poprawiona konfiguracja zaworów (inny dostawca, inne parametry, zaostrzone kontrole).
  - Routing `v2` – dodany krok „Valve flow pre-check” przed testem funkcjonalnym.
  - Część zleceń na BOM `v2` jest zatrzymana lub anulowana, pojawiają się nowe zlecenia na BOM `v3`.

- **MES:**
  - W `production_batches.json` pojawiają się partie „walidacyjne” na BOM `v3` – niskie/zerowe odsetki braków funkcjonalnych.
  - W `quality_checks.json`:
    - w starszych partiach (BOM `v2`) widoczne defekty `VALVE_FLOW_VARIATION`,
    - w nowych partiach (BOM `v3`, routing `v2`) defekty przepływu znikają, zostają głównie drobne defekty kosmetyczne.
  - `downtime_log.json` zawiera planowane przestoje związane z wdrożeniem nowych kroków routingu i kalibracją stanowisk.
  - `shift_log.json` oznacza zmiany wdrożeniowe i zmiany walidacyjne.

### 5.4. Snapshot 4 – `2026-03-30`  
**Utrzymanie stabilnej produkcji po działaniach korygujących**

- **ERP:**
  - BOM `v3` jest aktywną, stabilną wersją.
  - Routing `v2` jest utrzymywany bez dalszych zmian.
  - Nowe zlecenia (np. dla rezerwy narodowej, kolejnych szpitali) realizowane są już wyłącznie w oparciu o „dobrą” konfigurację.

- **MES:**
  - `production_batches.json` pokazuje serie partii z niskim lub zerowym odsetkiem braków funkcjonalnych.
  - `quality_checks.json` zawiera głównie:
    - pozytywne wyniki testów,
    - sporadyczne, pojedyncze defekty kosmetyczne (np. `SCRATCH_HOUSING`).
  - `downtime_log.json` to głównie przestoje planowane (prewencja, kalibracja), niewiele zdarzeń awaryjnych.
  - `shift_log.json` reprezentuje „nudne”, stabilne zmiany – świetne do prezentacji trendów i pokazania, że system pomaga „przejść od kryzysu do stabilności”.

---

## 6. Jak korzystać z tych danych w projekcie

1. **Backend (Django / DRF)**:
   - może mapować JSON-y z `erp/` i `mes/` na modele (np. `WorkOrder`, `ProductionBatch`, `QualityCheck`),
   - może integrować się z mockiem przez API:
     - `GET /erp?version=...`,
     - `GET /mes?version=...`,
     - `GET /docs/...`,
   - może udostępniać użytkownikowi przekrojowe widoki:
     - trend braków w czasie,
     - porównanie jakości między BOM `v1` / `v2` / `v3`,
     - wpływ zmian routingu na metryki jakości.

2. **Agenty AI (RAG)**:
   - mogą korzystać jednocześnie z:
     - dokumentów PDF w `docs/ventilator_pb560/` (wymagania, procedury, schematy),
     - danych ERP/MES z poszczególnych migawek,
   - aby odpowiadać na pytania typu:
     - „Dlaczego w styczniu 2026 wzrosła liczba braków?”
     - „Jakie działania korygujące wprowadzono w lutym?”
     - „Jaka jest różnica między BOM v2 a BOM v3 i jak przełożyło się to na defekty?”

3. **Prezentacja aplikacji / demo**:
   - można pokazać przełączenie się między migawkami (np. z `2026-01-31` na `2026-03-30`),
   - można wizualizować na wykresach:
     - odsetek braków w czasie,
     - liczbę przestojów planowanych vs nieplanowanych,
     - ewolucję zleceń i wersji BOM.

---

## 7. Rozszerzanie danych w przyszłości

Jeśli w przyszłości zajdzie potrzeba rozszerzenia danych:

- **Nowa migawka**:
  - dodać nowy folder `erp/YYYY-MM-DD/` i `mes/YYYY-MM-DD/` z tym samym zestawem plików,
  - zaktualizować `manifest.json` (dodać datę do `versions`, ewentualnie ustawić `latest`),
  - utrzymać spójność narracji (kontynuacja historii: np. dalsza optymalizacja, zmiana wolumenów, nowe typy defektów).

- **Nowy typ pliku**:
  - dodać plik np. `capacity_plan.json` lub `inventory_levels.json`,
  - dopisać odpowiednią sekcję w tym dokumencie (opis pliku, pól i roli w scenariuszu).

Dopóki zachowujemy **spójność struktur** opisanych w rozdziałach 3 i 4, wszystkie warstwy systemu (mock API, backend, agenty AI, frontend) będą mogły w przewidywalny sposób korzystać z danych ERP/MES.
