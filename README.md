# AeroOps AI

**Explainable Airline Disruption-Recovery Decision-Support Workbench**

AeroOps AI is a portfolio project that demonstrates how an airline operations
team could identify passengers affected by a disruption, evaluate constrained
recovery options, review policy evidence, approve a recommendation, and prepare
notification previews.

> This repository is an independent educational project. It uses a fictional
> airline and synthetic passenger data. It is not affiliated with Emirates or
> any other airline, and it does not perform real bookings or communications.

## Current Status: Day 1 Data Milestone

See [Day 1 verification](docs/DAY1_VERIFICATION.md) for measured counts,
test coverage, command results, and unresolved Git/timezone/index limitations.

Day 1 now prepares a real public-data foundation for the five-day MVP:

- OurAirports `airports.csv` and `countries.csv` are recorded with provenance.
- BTS Reporting Carrier On-Time Performance January 2025 is streamed from the
  local downloaded CSV or ZIP.
- Focus airports are `JFK`, `ATL`, `ORD`, `DFW`, `LAX`, and `SFO`.
- Historical public schedules are stored separately from synthetic operational
  demo data.
- The DFW-centered demo uses traceable BTS schedule rows only as schedule
  shapes. Passenger, booking, seat inventory, policy, and disruption records
  are explicitly synthetic.
- SQLite is used for the local MVP database.

NOAA weather and machine-learning training are intentionally not part of Day 1.

## Data Layout

```text
data/
  raw/         downloaded source files, ignored by Git
  processed/   generated SQLite database, ignored by Git
```

The importer does not download duplicate files. It uses the downloaded files
already placed under `data/raw`.

## Windows Quick Start

Open PowerShell from the project root:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1
python -m pip install -r backend\requirements.txt
cd backend
python -m app.day1_data import
python -m pytest -q
```

Expected import summary from the current downloaded files:

```text
AeroOps Day 1 data import complete
Imported counts:
  public_airports: 6
  bts_rows_scanned: 539747
  historical_flights: 196701
  historical_rows_skipped_missing_required: 0
Validation:
  PASS source_hashes_recorded
  PASS focus_airport_count
  PASS historical_flight_count
  PASS historical_required_fields
  PASS historical_duplicate_records
  PASS synthetic_passenger_labels
  PASS synthetic_demo_present
```

Expected backend test result:

```text
5 passed
```

## Run The App

In one PowerShell terminal:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\backend
$env:DATABASE_URL = "sqlite:///C:/Users/sumiy/Documents/sumiya/OneDrive/Desktop/AeroOps_AI_Day1/data/processed/aeroops_day1.sqlite"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

- Dashboard: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Day 1 API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/v1/demo/summary` | Seeded scenario counts and disruption |
| POST | `/api/v1/demo/reset` | Restore deterministic synthetic demo data |
| GET | `/api/v1/disruptions/{id}/affected-passengers` | Detect affected passengers |
| GET | `/api/v1/audit-logs` | Review recorded scenario actions |

## Important Limitations

- This is a decision-support demonstration, not a production airline system.
- Public BTS rows describe historical schedules; the demo cancellation is
  synthetic unless the source row itself says otherwise.
- All passenger names, booking references, seat inventory, and policies are
  synthetic.
- No real passenger data or confidential airline policy is used.
- No performance, accuracy, user, or business-impact claims have been made.

Use [`docs/DAY1_GUIDE.md`](docs/DAY1_GUIDE.md) for the step-by-step learning
workflow.
