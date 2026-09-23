# Day 1 Verification - 2026-09-23

Verification completed with limitations below. No recovery engine was built.
The original public historical tables were not deleted or re-imported.
An isolated import was run in `data/processed/day1_verification.sqlite`.
Both directions of a SQL EXCEPT comparison found zero historical-row differences.

## Verified Facts

| Check | Observed result |
|---|---|
| Public focus airports | 6: ATL, DFW, JFK, LAX, ORD, SFO |
| Raw OurAirports matches | Exactly one US large_airport per focus code; KATL, KDFW, KJFK, KLAX, KORD, KSFO |
| Historical flights | 196701 |
| Historical date range | 2025-01-01 through 2025-01-31 |
| Isolated import rows scanned | 539747 |
| Rows skipped for missing required values | 0 |
| Missing historical scheduled times | 0 |
| Duplicate business-key groups | 0 (date, airline, flight number, origin, destination, scheduled departure and arrival) |
| Demo airports / flights | 6 / 20 |
| Simulated cancellations / disruptions | 1 / 1 |
| Simulated cancellation | ANV101, ORD -> DFW, stored departure 2025-01-01 05:00:00 |
| Direct scheduled demo alternatives | 2, strictly later and no more than 24 hours later |
| Alternatives | ANV106 at 06:00; ANV118 at 07:09, both ORD -> DFW on January 1 |
| Provenance | 20/20 demo flights resolve through audit JSON to historical rows and matching raw CSV rows |
| Cancellation source | Historical ID 1806; source row 2466; AA 370; BTS Cancelled=0 |
| Passengers / bookings | 50 / 50, synthetic |
| Affected passengers | 12 |
| Synthetic passenger names and references | 50/50 |
| Inventory | Embedded in all 20 flight rows; no separate inventory table |
| Available inventory totals | 184 economy, 48 business, 20 accessibility slots, all synthetic |
| Accessibility needs | 2 synthetic passenger records |
| Positive accessibility inventory | 13 flight rows; accessibility field exists on all 20 |
| Policy table / policy records | No policy table; no stored policy records |
| Audit classification | SYNTHETIC |
| SQLite foreign-key check | No violations |
| Source files | 3; all recomputed SHA-256 hashes and byte sizes match |
| Retrieval dates | Unknown, NULL; filesystem modification times are separate |

Alternative counts use stored schedule clocks, not verified UTC instants. They
are demo candidates only; no capacity, cabin, group or policy feasibility is implied.
All demo airline identity, cancellation, passenger, booking and inventory data
is synthetic. The AA identifier above is public source provenance only.

Recomputed source hashes:

```text
airports.csv  afee98cc969c6564a76807bee54859e0727b7b4e68421c0ab05967cd0c5a76ea
countries.csv 2a9dbee691125b0cdb8ceb5fe227c48c903f99c488963b8e53e2ab366521c639
BTS January   d7c7d59452cad1215d9605e8ff350a4bad7282750765084fe57928a5ad275453
```

## Remaining Issues And Limits

- Git checks fail: this folder has no `.git` repository. Committed-file searches,
  history review and confirmation of tracked/untracked data are unproven.
  `.gitignore` has rules for raw data, processed data and SQLite files, but ignore
  rules alone do not prove that previously tracked files are excluded.
- The source readme explicitly defines BTS schedule times as local clock times.
  `seed._combine_date_time` attaches UTC without converting; the response schema
  adds `Z` to SQLite's offset-free value and the frontend labels it UTC. The smoke
  response was `2025-01-01T05:00:00Z`, which is not a verified UTC departure.
  Arrival rollover is also approximated with a two-hour fallback. Schedule
  timezone normalization remains unresolved; no public rows were changed.
- Demo provenance is in audit JSON, not a foreign key on each flight. Every
  current link resolves, but the database does not enforce that relationship.
  Source-file hashes are recorded; source-row hashes do not exist.
- Both flight tables have origin and destination indexes. Historical flights
  also have flight-date, source-file, source-row-number and unique source-record-key
  indexes. Neither table has a scheduled-departure index. The unique source key
  contains the row number and is not a content hash. The source-file SHA index
  does not substitute for a source-row hash index.
- Existing validation checks only source-hash uniqueness, not recomputation;
  airport count, not airport identity; positive historical count, not January
  coverage; and only five NULL fields, not every required field. Duplicate
  source-key validation includes the row number. The independent verification
  adds evidence for the current data, not comprehensive importer regression tests.
- The importer buffers ORM objects until commit even though CSV reading is
  streamed. It commits table deletion before loading, and filename selection
  `2025_1*` could also select October-December. These are importer robustness gaps.
  ZIP handling was inspected but not exercised: the downloaded source is CSV.
- README and DAY1_GUIDE contain this machine's absolute paths. App configuration
  defaults to `./aeroops.db`, whereas the importer defaults to the processed
  database. Set DATABASE_URL explicitly when launching FastAPI.
- Source-text searches found no matching credential literals, private keys,
  email addresses, phone or passport data. This is a pattern-based local scan,
  not proof of absence and not a Git-history audit. Passenger names are generated
  as `Synthetic Passenger NNN`. No real passenger/payment data was observed.
- Emirates appears in an explicit non-affiliation disclaimer and PROJECT_PLAN
  wording about avoiding branding and a resume. No affiliation claim or logo
  was found in the inspected application. That resume wording remains.
- The demo-reset endpoint is unauthenticated and resets synthetic tables. Keep
  this demo local; the smoke check made GET requests only.

## What Tests Actually Assert

The original five tests create a fresh in-memory database. No BTS data is loaded;
the fallback schedule is used, including DFW -> LAX, unlike the actual imported
demo's ORD -> DFW cancellation.

1. Summary is HTTP 200; counts are 6 airports, 20 flights, 50 passengers,
   50 bookings, 1 disruption, 12 affected; ANV101 is DFW -> LAX in the fallback.
2. Affected-passenger endpoint is HTTP 200 with 12 entries, SYN-P references,
   five specific group codes, two business passengers and two accessibility needs.
3. Missing disruption returns HTTP 404 with `Disruption not found`.
4. Two resets each return HTTP 200 and 12 affected; audit endpoint is HTTP 200
   with reset action and SYNTHETIC text. This does not compare all rows for determinism.
5. Health returns HTTP 200 and exact status/service/version fields.

Two new parametrized cases assert that import and validate CLI paths exit 1
when their validation result is FAIL, and that failure is printed. They mock
the data operations and do not exercise the importer.

## Changes

- `backend/app/day1_data.py`: nonzero exit status when validation reports FAIL.
- `backend/app/verify_day1.py`: repeatable read-only evidence report on the existing
  processed database, including source hashes, raw-row traces, counts and indexes.
  This prints evidence; it is not a comprehensive acceptance gate.
- `backend/tests/test_day1_cli.py`: two failure-exit regression cases.
- `README.md`: link to this report.
- `docs/DAY1_VERIFICATION.md`: this report.

Generated changes: validation-results rows refreshed in the original SQLite file;
isolated verification SQLite created; frontend node_modules, dist, TypeScript build
outputs and Python caches generated. These are covered by existing ignore rules.
No source datasets, existing synthetic rows or public historical rows were modified.

## Commands And Actual Results

Commands used PowerShell. `root` means the existing project folder, `backend`
and `frontend` mean its subdirectories. Read-command results below are condensed
to avoid copying entire source files into this report. Exit codes are explicit.

| Directory | Command | Actual output/result | Exit |
|---|---|---|---:|
| root | `git status --short` (initial and final) | fatal: not a git repository (or any of the parent directories): .git | 1 |
| root | `rg --files -g '!data/raw/**' -g '!node_modules/**' -g '!frontend/node_modules/**'` | Listed backend, frontend, docs, processed DB and Python caches | 0 |
| root | `Get-Content README.md,backend/requirements.txt,backend/pyproject.toml,frontend/package.json,.gitignore` | Read docs, Python dependencies/pytest config, build script and ignore rules | 0 |
| root | `Get-Content backend/app/day1_data.py` | Read importer/validator and deletion/commit behavior | 0 |
| root | `Get-Content backend/app/models.py,backend/app/seed.py` | Read public/synthetic models and seeding | 0 |
| root | `Get-Content backend/tests/*.py,backend/app/database.py,backend/app/config.py,backend/app/main.py,backend/app/services/*.py,backend/app/routers/*.py` | Read actual assertions, DB approach, startup, services and routes | 0 |
| root | `Get-Content backend/app/models.py,backend/app/day1_data.py \| Select-Object -Last 190` | Read final importer/validator portion | 0 |
| root | `Get-Content backend/app/models.py` | Read complete model definitions | 0 |
| root | `Get-Content backend/app/seed.py \| Select-Object -First 110` | Read fallback schedules and UTC attachment | 0 |
| backend | `python -m app.day1_data validate` (before and after fix) | All seven original checks PASS; exact output below | 0 |
| backend | `python -m pytest -q` (before fix) | 5 passed in 0.22s | 0 |
| frontend | `npm run build` | npm.ps1 cannot be loaded because running scripts is disabled | 1 |
| root | Source scan A below | Machine-specific doc paths; synthetic display_name fields; Emirates disclaimer/resume wording; policy references | 0 |
| frontend | `npm.cmd run build` (before install) | 'tsc' is not recognized as an internal or external command | 1 |
| root | `Get-Content docs/DAY1_GUIDE.md,frontend/src/App.tsx,frontend/src/api.ts` | Read guide, UI date formatting and API client | 0 |
| frontend | `npm.cmd ci --no-audit --no-fund` (sandbox) | npm error Exit handler never called! Log directory write error | 1 |
| backend | `python -m app.verify_day1` | JSON evidence: counts, all 20 valid links/raw rows, three matching hashes, zero duplicate groups/FK violations; facts above | 0 |
| backend | `$env:DATABASE_URL = 'sqlite:///../data/processed/day1_verification.sqlite'` then `python -m app.day1_data import` | 539747 scanned, 196701 imported, 6 airports, 0 skipped; seven PASS results | 0 |
| root | `git ls-files` | fatal: not a git repository (or any of the parent directories): .git | 1 |
| root | `Get-ChildItem -Force -Name` | .qodo, backend, data, docs, frontend, .env.example, .gitignore, LICENSE, README.md | 0 |
| root | `rg -n -i 'CRSDepTime\|CRSArrTime\|local' data/raw/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1/readme.html` | CRSDepTime/CRSArrTime explicitly local time, plus other local-time fields | 0 |
| frontend | `npm.cmd ci --no-audit --no-fund` (approved retry) | added 68 packages in 6s | 0 |
| root | `Get-Content .env.example` | DATABASE_URL=sqlite:///./aeroops.db; FRONTEND_ORIGINS=http://localhost:5173 | 0 |
| root | Hidden-file listing below | Source files plus environment examples; no .git folder | 0 |
| backend | `python -m pytest -q` (after fix) | 7 passed in 0.19s | 0 |
| frontend | `npm.cmd run build` (after install, sandbox) | esbuild: Access is denied; could not resolve vite.config.ts | 1 |
| backend | Live smoke Python script below | health, OpenAPI, demo summary HTTP 200; server stopped | 0 |
| root | `Get-Content backend/app/schemas.py,frontend/vite.config.ts,frontend/.env.example` | Read forced UTC serializer, Vite config and API URL | 0 |
| frontend | `npm.cmd run build` (approved retry) | Vite 5.4.21; 32 modules transformed; built in 1.14s | 0 |
| root | Source scan B below | No matches | 1 |
| backend | Comparison Python script below | 2 alternatives; source Cancelled=0; inventory 184/48/20; zero historical differences both directions; six unique raw airport matches | 0 |

Source scan A:

```powershell
rg -n -i --glob '!package-lock.json' --glob '!data/**' --glob '!**/__pycache__/**' --glob '!**/node_modules/**' --glob '!**/dist/**' 'C:\\Users\\|C:/Users/|/home/|/Users/|Emirates|api[_-]?key|secret|password|passport|payment|email|phone|display_name' README.md docs backend frontend .gitignore
```

Hidden-file listing:

```powershell
rg --files --hidden -g '!data/**' -g '!**/node_modules/**' -g '!**/__pycache__/**' -g '!**/.pytest_cache/**' -g '!**/dist/**'
```

Source scan B (exit 1 means no matches, not a scanner failure):

```powershell
rg -n -i --hidden -g '!data/**' -g '!**/node_modules/**' -g '!**/__pycache__/**' -g '!**/.pytest_cache/**' -g '!**/dist/**' -g '!**/*.tsbuildinfo' '(sk-[A-Za-z0-9_-]{16,}|AKIA[A-Z0-9]{16}|ghp_[A-Za-z0-9]+|BEGIN .*PRIVATE KEY|api[_-]?key\s*[:=]|secret\s*[:=]|password\s*[:=]|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|passport|credit.?card|phone)' .
```

Validator output, before and after fix:

```text
AeroOps Day 1 validation complete
  PASS source_hashes_recorded: {'source_files': 3, 'unique_sha256_hashes': 3}
  PASS focus_airport_count: {'public_airports': 6}
  PASS historical_flight_count: {'historical_flights': 196701}
  PASS historical_required_fields: {'missing_rows': 0}
  PASS historical_duplicate_records: {'duplicates': 0}
  PASS synthetic_passenger_labels: {'non_synthetic_refs': 0}
  PASS synthetic_demo_present: {'disruptions': 1, 'bookings': 50}
```

Live smoke script was passed to `python -` using PowerShell `@' ... '@`:

```python
import os, subprocess, sys, time, urllib.request, json
from pathlib import Path
root = Path.cwd().parent
env = dict(os.environ, DATABASE_URL='sqlite:///' + (root/'data/processed/aeroops_day1.sqlite').as_posix())
process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8765'], env=env)
try:
    for attempt in range(50):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=1) as response:
                print('/health', response.status, response.read().decode())
            break
        except OSError:
            if process.poll() is not None:
                raise RuntimeError('Server exited before health check')
            time.sleep(0.2)
    else:
        raise RuntimeError('Server did not become ready')
    for path in ['/openapi.json', '/api/v1/demo/summary']:
        with urllib.request.urlopen('http://127.0.0.1:8765'+path) as response:
            payload = json.load(response)
            print(path, response.status, json.dumps(payload if path.endswith('summary') else sorted(payload['paths'])))
finally:
    process.terminate()
    process.wait(timeout=10)
    print('Smoke server stopped')
```

Smoke output: health 200 with `status=ok`, `service=AeroOps AI`,
`version=0.1.0-day1`; OpenAPI 200 with all five existing routes; summary 200
with 6 airports, 20 flights, 50 passengers, 50 bookings, 1 disruption and 12
affected. Cancellation ANV101 ORD -> DFW, timestamp `2025-01-01T05:00:00Z`.
The UTC suffix is the unresolved issue described above. Server was stopped.

Comparison script was also passed to `python -` with a PowerShell here-string:

```python
import csv, sqlite3
from pathlib import Path
root = Path.cwd().parent
with sqlite3.connect('file:../data/processed/aeroops_day1.sqlite?mode=ro', uri=True) as db:
    print('Alternatives:', db.execute('SELECT id, flight_number, origin_code, destination_code, scheduled_departure FROM flights WHERE id IN (6,18)').fetchall())
    print('Cancelled source:', db.execute('SELECT id, reporting_airline, flight_number, source_row_number, cancelled FROM historical_flights WHERE id=1806').fetchall())
    print('Inventory totals:', db.execute('SELECT sum(available_economy),sum(available_business),sum(accessible_slots_available) FROM flights').fetchone())
    db.execute("ATTACH DATABASE 'file:../data/processed/day1_verification.sqlite?mode=ro' AS verification")
    for left, right in [('main','verification'),('verification','main')]:
        print('Historical difference', left, right, db.execute(f'SELECT count(*) FROM (SELECT * FROM {left}.historical_flights EXCEPT SELECT * FROM {right}.historical_flights)').fetchone()[0])
with (root/'data/raw/airports.csv').open(encoding='utf-8-sig', newline='') as stream:
    matches = {code: [] for code in ['ATL','DFW','JFK','LAX','ORD','SFO']}
    for row in csv.DictReader(stream):
        if row['iata_code'] in matches:
            matches[row['iata_code']].append((row['ident'],row['iso_country'],row['type']))
    print('Raw airport matches:', matches)
```

Manual source/document edits used apply_patch successfully, not shell writes.

## Repeat The Non-Destructive Checks

Open PowerShell at the project root:

```powershell
cd backend
python -m app.day1_data validate
python -m app.verify_day1
python -m pytest -q
cd ..\frontend
npm.cmd ci --no-audit --no-fund
npm.cmd run build
cd ..
git status --short
```

The final Git command will fail until this directory is actually a Git repository.
The validator refreshes only validation results; the evidence command is read-only.
Do not run a default import just to repair the synthetic scenario.

Recommended commit message, once Git is available:
`fix: fail Day 1 CLI on validation errors and document baseline verification`
