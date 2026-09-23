"""Import and validate the Day 1 public aviation data slice."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator
from zipfile import ZipFile

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, _engine_options
from app.models import (
    Booking,
    Disruption,
    HistoricalFlight,
    Passenger,
    PublicAirport,
    SourceFile,
    ValidationResult,
)
from app.seed import FOCUS_AIRPORTS, seed_demo_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_DB_PATH = PROCESSED_DIR / "aeroops_day1.sqlite"
FOCUS_CODES = {"JFK", "ATL", "ORD", "DFW", "LAX", "SFO"}

OURAIRPORTS_AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
OURAIRPORTS_COUNTRIES_URL = "https://davidmegginson.github.io/ourairports-data/countries.csv"
BTS_ON_TIME_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ"

BTS_REQUIRED_COLUMNS = {
    "FlightDate",
    "Reporting_Airline",
    "Flight_Number_Reporting_Airline",
    "Origin",
    "Dest",
    "CRSDepTime",
    "CRSArrTime",
    "Cancelled",
}

BTS_OPTIONAL_COLUMNS = {
    "DepTime",
    "ArrTime",
    "DepDelayMinutes",
    "ArrDelayMinutes",
    "CancellationCode",
    "Diverted",
    "Distance",
}


def _database_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def _session_factory() -> sessionmaker[Session]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(_database_url(), **_engine_options(_database_url()))
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_modified_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _source_file(db: Session, path: Path, source_name: str, origin_url: str | None) -> SourceFile:
    source = SourceFile(
        source_name=source_name,
        origin_url=origin_url,
        local_path=str(path.relative_to(PROJECT_ROOT)),
        size_bytes=path.stat().st_size,
        sha256=_sha256(path),
        retrieved_at=None,
        file_modified_at=_file_modified_at(path),
        retrieval_note=(
            "Retrieval date was not present in the downloaded file metadata; "
            "filesystem modified time is recorded separately."
        ),
    )
    db.add(source)
    db.flush()
    return source


def _find_first(patterns: Iterable[str]) -> Path:
    for pattern in patterns:
        matches = sorted(RAW_DIR.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"Could not find any of these files in {RAW_DIR}: {patterns}")


def _find_bts_january_file() -> Path:
    patterns = [
        "**/*2025_1*.zip",
        "**/*2025_1*.csv",
        "**/On_Time_Reporting_Carrier_On_Time_Performance*(1987_present)*2025_1*.csv",
    ]
    return _find_first(patterns)


@contextmanager
def _open_bts_text(path: Path) -> Iterator[io.TextIOBase]:
    if path.suffix.lower() == ".zip":
        with ZipFile(path) as archive:
            csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if len(csv_names) != 1:
                raise ValueError(f"Expected one CSV inside {path}, found {len(csv_names)}")
            with archive.open(csv_names[0]) as member:
                wrapper = io.TextIOWrapper(member, encoding="utf-8-sig", newline="")
                yield wrapper
    else:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            yield file


def _clean_headers(headers: Iterable[str | None]) -> list[str]:
    return [header for header in headers if header]


def inspect_headers(airports_path: Path, countries_path: Path, bts_path: Path) -> dict:
    with airports_path.open("r", encoding="utf-8-sig", newline="") as file:
        airports_headers = next(csv.reader(file))
    with countries_path.open("r", encoding="utf-8-sig", newline="") as file:
        countries_headers = next(csv.reader(file))
    with _open_bts_text(bts_path) as file:
        bts_headers = _clean_headers(next(csv.reader(file)))

    missing_bts = sorted(BTS_REQUIRED_COLUMNS - set(bts_headers))
    return {
        "airports_headers": airports_headers,
        "countries_headers": countries_headers,
        "bts_headers": bts_headers,
        "bts_missing_required_columns": missing_bts,
        "bts_optional_columns_present": sorted(BTS_OPTIONAL_COLUMNS & set(bts_headers)),
    }


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _parse_bool_number(value: str | None) -> bool:
    return str(value or "0").strip() in {"1", "1.0", "true", "True"}


def _parse_bts_time(value: str | None):
    if value is None or value == "":
        return None
    padded = value.strip().split(".")[0].zfill(4)
    hour = int(padded[:2])
    minute = int(padded[2:])
    if hour == 24:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    from datetime import time

    return time(hour, minute)


def _parse_date(value: str):
    from datetime import date

    year, month, day = [int(part) for part in value.split("-")]
    return date(year, month, day)


def _load_airports(db: Session, airports_path: Path, countries_path: Path) -> dict:
    airports_source = _source_file(
        db, airports_path, "OurAirports airports.csv", OURAIRPORTS_AIRPORTS_URL
    )
    _source_file(db, countries_path, "OurAirports countries.csv", OURAIRPORTS_COUNTRIES_URL)

    matches_by_iata: dict[str, list[dict[str, str]]] = {code: [] for code in FOCUS_CODES}
    with airports_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = (row.get("iata_code") or "").strip().upper()
            if code in FOCUS_CODES:
                matches_by_iata[code].append(row)

    failures: list[str] = []
    for code, matches in sorted(matches_by_iata.items()):
        appropriate = [
            row
            for row in matches
            if row.get("iso_country") == "US"
            and row.get("type") in {"large_airport", "medium_airport"}
        ]
        if len(matches) != 1 or len(appropriate) != 1:
            failures.append(
                f"{code}: total_matches={len(matches)}, appropriate_us_matches={len(appropriate)}"
            )
            continue
        row = appropriate[0]
        db.add(
            PublicAirport(
                iata_code=code,
                ident=row["ident"],
                airport_type=row["type"],
                name=row["name"],
                municipality=row.get("municipality") or None,
                iso_country=row["iso_country"],
                iso_region=row.get("iso_region") or None,
                latitude_deg=_parse_float(row.get("latitude_deg")),
                longitude_deg=_parse_float(row.get("longitude_deg")),
                source_file_id=airports_source.id,
            )
        )

    if failures:
        raise ValueError("Airport validation failed: " + "; ".join(failures))
    return {"public_airports": len(FOCUS_CODES)}


def _load_bts_flights(db: Session, bts_path: Path) -> dict:
    bts_source = _source_file(
        db,
        bts_path,
        "BTS Reporting Carrier On-Time Performance January 2025",
        BTS_ON_TIME_URL,
    )
    imported = 0
    scanned = 0
    missing_required_rows = 0
    duplicate_keys: Counter[str] = Counter()

    with _open_bts_text(bts_path) as file:
        reader = csv.DictReader(file)
        fieldnames = set(_clean_headers(reader.fieldnames or []))
        missing = BTS_REQUIRED_COLUMNS - fieldnames
        if missing:
            raise ValueError(f"BTS file is missing required columns: {sorted(missing)}")

        for row_number, row in enumerate(reader, start=2):
            scanned += 1
            origin = (row.get("Origin") or "").strip().upper()
            dest = (row.get("Dest") or "").strip().upper()
            if origin not in FOCUS_CODES and dest not in FOCUS_CODES:
                continue

            required_values = [
                row.get("FlightDate"),
                row.get("Reporting_Airline"),
                row.get("Flight_Number_Reporting_Airline"),
                origin,
                dest,
                row.get("CRSDepTime"),
                row.get("CRSArrTime"),
                row.get("Cancelled"),
            ]
            if any(value in {None, ""} for value in required_values):
                missing_required_rows += 1
                continue

            source_record_key = (
                f"{row['FlightDate']}|{row['Reporting_Airline']}|"
                f"{row['Flight_Number_Reporting_Airline']}|{origin}|{dest}|"
                f"{row['CRSDepTime']}|{row['CRSArrTime']}|{row_number}"
            )
            duplicate_keys[source_record_key] += 1
            db.add(
                HistoricalFlight(
                    source_file_id=bts_source.id,
                    flight_date=_parse_date(row["FlightDate"]),
                    reporting_airline=row["Reporting_Airline"].strip().upper(),
                    flight_number=row["Flight_Number_Reporting_Airline"].strip(),
                    origin_code=origin,
                    destination_code=dest,
                    scheduled_departure_time=_parse_bts_time(row.get("CRSDepTime")),
                    scheduled_arrival_time=_parse_bts_time(row.get("CRSArrTime")),
                    actual_departure_time=_parse_bts_time(row.get("DepTime")),
                    actual_arrival_time=_parse_bts_time(row.get("ArrTime")),
                    departure_delay_minutes=_parse_float(row.get("DepDelayMinutes")),
                    arrival_delay_minutes=_parse_float(row.get("ArrDelayMinutes")),
                    cancelled=_parse_bool_number(row.get("Cancelled")),
                    cancellation_code=row.get("CancellationCode") or None,
                    diverted=_parse_bool_number(row.get("Diverted")),
                    distance_miles=_parse_float(row.get("Distance")),
                    source_row_number=row_number,
                    source_record_key=source_record_key,
                )
            )
            imported += 1

    duplicate_count = sum(count - 1 for count in duplicate_keys.values() if count > 1)
    if duplicate_count:
        raise ValueError(f"Found {duplicate_count} duplicate BTS source record keys")
    return {
        "bts_rows_scanned": scanned,
        "historical_flights": imported,
        "historical_rows_skipped_missing_required": missing_required_rows,
    }


def _record_validation(db: Session, check_name: str, status: str, details: dict) -> None:
    db.add(
        ValidationResult(
            check_name=check_name,
            status=status,
            details_json=json.dumps(details, sort_keys=True, default=str),
        )
    )


def validate_day1_data(db: Session) -> list[dict]:
    db.execute(delete(ValidationResult))
    results: list[dict] = []

    def add(check_name: str, passed: bool, details: dict) -> None:
        status = "PASS" if passed else "FAIL"
        payload = {"check_name": check_name, "status": status, "details": details}
        results.append(payload)
        _record_validation(db, check_name, status, details)

    source_count = db.scalar(select(func.count()).select_from(SourceFile)) or 0
    unique_hashes = db.scalar(select(func.count(func.distinct(SourceFile.sha256)))) or 0
    add(
        "source_hashes_recorded",
        source_count >= 3 and source_count == unique_hashes,
        {"source_files": source_count, "unique_sha256_hashes": unique_hashes},
    )

    airport_count = db.scalar(select(func.count()).select_from(PublicAirport)) or 0
    add("focus_airport_count", airport_count == 6, {"public_airports": airport_count})

    flight_count = db.scalar(select(func.count()).select_from(HistoricalFlight)) or 0
    add("historical_flight_count", flight_count > 0, {"historical_flights": flight_count})

    missing_fields = db.scalar(
        select(func.count())
        .select_from(HistoricalFlight)
        .where(
            (HistoricalFlight.flight_date.is_(None))
            | (HistoricalFlight.reporting_airline.is_(None))
            | (HistoricalFlight.flight_number.is_(None))
            | (HistoricalFlight.origin_code.is_(None))
            | (HistoricalFlight.destination_code.is_(None))
        )
    ) or 0
    add("historical_required_fields", missing_fields == 0, {"missing_rows": missing_fields})

    duplicate_records = db.scalar(
        select(func.count())
        .select_from(
            select(HistoricalFlight.source_record_key)
            .group_by(HistoricalFlight.source_record_key)
            .having(func.count() > 1)
            .subquery()
        )
    ) or 0
    add("historical_duplicate_records", duplicate_records == 0, {"duplicates": duplicate_records})

    synthetic_refs = db.scalar(
        select(func.count())
        .select_from(Passenger)
        .where(Passenger.synthetic_ref.not_like("SYN-%"))
    ) or 0
    add("synthetic_passenger_labels", synthetic_refs == 0, {"non_synthetic_refs": synthetic_refs})

    synthetic_disruptions = db.scalar(select(func.count()).select_from(Disruption)) or 0
    bookings = db.scalar(select(func.count()).select_from(Booking)) or 0
    add(
        "synthetic_demo_present",
        synthetic_disruptions == 1 and bookings == 50,
        {"disruptions": synthetic_disruptions, "bookings": bookings},
    )

    db.commit()
    return results


def import_day1_data() -> dict:
    airports_path = _find_first(["airports.csv"])
    countries_path = _find_first(["countries.csv"])
    bts_path = _find_bts_january_file()
    header_report = inspect_headers(airports_path, countries_path, bts_path)
    if header_report["bts_missing_required_columns"]:
        raise ValueError(
            "Cannot import BTS data; missing required columns: "
            + ", ".join(header_report["bts_missing_required_columns"])
        )

    SessionLocal = _session_factory()
    with SessionLocal() as db:
        for model in (ValidationResult, HistoricalFlight, PublicAirport, SourceFile):
            db.execute(delete(model))
        db.commit()

        counts = {}
        counts.update(_load_airports(db, airports_path, countries_path))
        counts.update(_load_bts_flights(db, bts_path))
        db.commit()

        seed_demo_data(db)
        validation_results = validate_day1_data(db)

    return {
        "database_url": _database_url(),
        "airports_file": str(airports_path.relative_to(PROJECT_ROOT)),
        "countries_file": str(countries_path.relative_to(PROJECT_ROOT)),
        "bts_file": str(bts_path.relative_to(PROJECT_ROOT)),
        "header_report": {
            "bts_required_columns_present": sorted(BTS_REQUIRED_COLUMNS),
            "bts_optional_columns_present": header_report["bts_optional_columns_present"],
        },
        "counts": counts,
        "validation_results": validation_results,
    }


def print_report(report: dict) -> None:
    print("AeroOps Day 1 data import complete")
    print(f"Database: {report['database_url']}")
    print(f"OurAirports airports: {report['airports_file']}")
    print(f"OurAirports countries: {report['countries_file']}")
    print(f"BTS January 2025 file: {report['bts_file']}")
    print("Imported counts:")
    for key, value in report["counts"].items():
        print(f"  {key}: {value}")
    print("Validation:")
    for result in report["validation_results"]:
        print(f"  {result['status']} {result['check_name']}: {result['details']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["import", "validate"], help="Day 1 data action")
    args = parser.parse_args()

    if args.command == "import":
        report = import_day1_data()
        print_report(report)
        if any(result["status"] != "PASS" for result in report["validation_results"]):
            raise SystemExit(1)
        return

    SessionLocal = _session_factory()
    with SessionLocal() as db:
        results = validate_day1_data(db)
    print("AeroOps Day 1 validation complete")
    for result in results:
        print(f"  {result['status']} {result['check_name']}: {result['details']}")
    if any(result["status"] != "PASS" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
