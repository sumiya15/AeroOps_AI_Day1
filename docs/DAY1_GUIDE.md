# Day 1 Guide: Public Flight Data Foundation

## Objective

Prepare the first real data layer for the AeroOps AI MVP:

`downloaded raw files -> provenance -> SQLite public tables -> synthetic DFW demo -> validation`

Keep NOAA weather and machine-learning training out of Day 1.

## What Is Real And What Is Synthetic

Real public data:

- OurAirports airport and country files.
- BTS Reporting Carrier On-Time Performance rows for January 2025.
- Airport codes and historical schedule rows.

Synthetic data:

- Fictional airline flights used by the app dashboard.
- The demo disruption.
- Passengers, bookings, groups, seat inventory, and policies.

The demo uses BTS schedule rows as traceable schedule shapes. It does not claim
that a historical flight was cancelled unless the BTS row says it was.

## Folder Layout

```text
data/
  raw/         downloaded CSV or ZIP files, kept out of Git
  processed/   generated SQLite database, kept out of Git
backend/
  app/day1_data.py   importer and validator
```

Your current raw files were moved into `data/raw`.

## Exact Windows Setup

Open PowerShell:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1
python -m pip install -r backend\requirements.txt
```

This installs FastAPI, SQLAlchemy, pytest, and the other backend packages.

## Import The Data

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\backend
python -m app.day1_data import
```

What the importer does:

1. Finds the downloaded OurAirports files and the January 2025 BTS file.
2. Reads headers before import and confirms required BTS columns exist.
3. Records each source file path, origin URL, size, modified time, and SHA-256.
4. Imports exactly the six focus airports from OurAirports.
5. Streams BTS rows and keeps flights where `Origin` or `Dest` is one of the
   six focus airports.
6. Normalizes dates, airport codes, schedule times, cancellation flags, delay
   values, and row-level provenance.
7. Seeds the DFW-centered synthetic demo.
8. Runs validation checks.

Expected successful output from the current files:

```text
AeroOps Day 1 data import complete
Database: sqlite:///C:/Users/sumiy/Documents/sumiya/OneDrive/Desktop/AeroOps_AI_Day1/data/processed/aeroops_day1.sqlite
OurAirports airports: data\raw\airports.csv
OurAirports countries: data\raw\countries.csv
BTS January 2025 file: data\raw\On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1\On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2025_1.csv
Imported counts:
  public_airports: 6
  bts_rows_scanned: 539747
  historical_flights: 196701
  historical_rows_skipped_missing_required: 0
Validation:
  PASS source_hashes_recorded: {'source_files': 3, 'unique_sha256_hashes': 3}
  PASS focus_airport_count: {'public_airports': 6}
  PASS historical_flight_count: {'historical_flights': 196701}
  PASS historical_required_fields: {'missing_rows': 0}
  PASS historical_duplicate_records: {'duplicates': 0}
  PASS synthetic_passenger_labels: {'non_synthetic_refs': 0}
  PASS synthetic_demo_present: {'disruptions': 1, 'bookings': 50}
```

## Validate Again Later

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\backend
python -m app.day1_data validate
```

Expected result:

```text
AeroOps Day 1 validation complete
  PASS source_hashes_recorded
  PASS focus_airport_count
  PASS historical_flight_count
  PASS historical_required_fields
  PASS historical_duplicate_records
  PASS synthetic_passenger_labels
  PASS synthetic_demo_present
```

## Run Tests

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\backend
python -m pytest -q
```

Expected result:

```text
5 passed
```

## Run The Backend

Use the processed SQLite database created by the importer:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\backend
$env:DATABASE_URL = "sqlite:///C:/Users/sumiy/Documents/sumiya/OneDrive/Desktop/AeroOps_AI_Day1/data/processed/aeroops_day1.sqlite"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

## Run The Frontend

Open a second PowerShell terminal:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Dashboard:

```text
http://localhost:5173
```

## Provenance Recorded

The current import recorded these source hashes:

| Source | Size bytes | SHA-256 |
|---|---:|---|
| OurAirports airports.csv | 12728855 | `afee98cc969c6564a76807bee54859e0727b7b4e68421c0ab05967cd0c5a76ea` |
| OurAirports countries.csv | 24583 | `2a9dbee691125b0cdb8ceb5fe227c48c903f99c488963b8e53e2ab366521c639` |
| BTS January 2025 CSV | 243177378 | `d7c7d59452cad1215d9605e8ff350a4bad7282750765084fe57928a5ad275453` |

The files did not contain retrieval dates. The importer records `retrieved_at`
as empty and stores the filesystem modified time separately.

## Day 1 Acceptance Checks

- Backend creates the schema without manual SQL.
- Source files have size and SHA-256 provenance.
- Six focus airports import from OurAirports and validate as unique US airports.
- January BTS rows are streamed instead of loaded all at once.
- Historical flights are separate from synthetic bookings and passengers.
- Demo disruption, passenger, booking, seat inventory, and policy data are
  synthetic.
- Validation passes for row counts, required fields, duplicates, hashes, airport
  matches, and synthetic labels.
- Backend tests pass.

## What Remains For Day 2

Day 2 can build recovery-option generation on top of this data:

- choose candidate alternate flights after a disruption;
- apply synthetic policy constraints;
- rank options with explainable scoring;
- keep audit trails for recommendations;
- still avoid real passenger data and confidential airline policies.
