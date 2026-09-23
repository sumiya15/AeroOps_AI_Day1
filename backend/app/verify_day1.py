"""Read-only evidence checks against the existing Day 1 SQLite database."""

import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta

from app.day1_data import DEFAULT_DB_PATH, PROJECT_ROOT, _open_bts_text


def verify():
    with sqlite3.connect(DEFAULT_DB_PATH.as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts = {t: db.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}
        flights = [dict(r) for r in db.execute("SELECT * FROM flights ORDER BY id")]
        cancelled = [r for r in flights if r['status'] == 'CANCELLED']
        target = cancelled[0]
        departure = datetime.fromisoformat(target['scheduled_departure'])
        alternatives = [r['id'] for r in flights if r['status'] == 'SCHEDULED'
                        and r['origin_code'] == target['origin_code']
                        and r['destination_code'] == target['destination_code']
                        and departure < datetime.fromisoformat(r['scheduled_departure']) <= departure + timedelta(hours=24)]
        sources = [dict(r) for r in db.execute("SELECT * FROM source_files")]
        for source in sources:
            path = PROJECT_ROOT / source['local_path']
            with path.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            source['recomputed_sha256'] = actual
            source['hash_matches'] = actual == source['sha256']
            source['size_matches'] = path.stat().st_size == source['size_bytes']
        audit = json.loads(db.execute("SELECT details_json FROM audit_logs WHERE action='DEMO_SCENARIO_RESET' ORDER BY id DESC LIMIT 1").fetchone()[0])
        traces = audit['historical_trace_rows']
        provenance = []
        raw_targets = {}
        for flight in flights:
            matches = [t for t in traces if t['synthetic_flight_id'] == flight['id']]
            valid = len(matches) == 1
            historical = []
            if valid:
                trace = matches[0]
                historical = db.execute("""SELECT * FROM historical_flights WHERE source_row_number=?
                    AND reporting_airline=? AND flight_number=? AND origin_code=? AND destination_code=? AND flight_date=?""",
                    (trace['bts_source_row_number'], trace['bts_reporting_airline'], trace['bts_flight_number'],
                     trace['bts_origin'], trace['bts_destination'], trace['bts_flight_date'])).fetchall()
                valid = len(historical) == 1
            if valid:
                row = dict(historical[0])
                valid = (flight['origin_code'] == row['origin_code'] and flight['destination_code'] == row['destination_code']
                         and flight['scheduled_departure'] == row['flight_date'] + ' ' + row['scheduled_departure_time']
                         and bool(row['cancelled']) == trace['bts_cancelled'])
                raw_targets.setdefault(row['source_file_id'], {})[row['source_row_number']] = row
            provenance.append({'demo_id': flight['id'], 'valid_database_link': valid,
                               'historical_id': historical[0]['id'] if len(historical) == 1 else None})
        raw_matches = 0
        for source_id, targets in raw_targets.items():
            source = next(s for s in sources if s['id'] == source_id)
            with _open_bts_text(PROJECT_ROOT / source['local_path']) as stream:
                for number, row in enumerate(csv.DictReader(stream), 2):
                    if number in targets:
                        h = targets[number]
                        raw_matches += int(all(row[key] == h[column] for key, column in (
                            ('FlightDate', 'flight_date'), ('Reporting_Airline', 'reporting_airline'),
                            ('Flight_Number_Reporting_Airline', 'flight_number'), ('Origin', 'origin_code'), ('Dest', 'destination_code')))
                            and bool(float(row['Cancelled'])) == bool(h['cancelled'])
                            and row['CRSDepTime'].zfill(4) == h['scheduled_departure_time'].replace(':', '')[:4])
                    if number >= max(targets):
                        break
        duplicates = db.execute("""SELECT count(*) FROM (SELECT 1 FROM historical_flights
            GROUP BY flight_date, reporting_airline, flight_number, origin_code, destination_code,
            scheduled_departure_time, scheduled_arrival_time HAVING count(*) > 1)""").fetchone()[0]
        result = {
            'counts': counts,
            'airports': [dict(r) for r in db.execute('SELECT iata_code, ident, iso_country, airport_type FROM public_airports ORDER BY iata_code')],
            'cancelled_flights': cancelled, 'direct_alternative_ids_within_24h': alternatives,
            'provenance': provenance, 'raw_source_rows_matched': raw_matches, 'source_files': sources,
            'business_key_duplicate_groups': duplicates,
            'missing_schedule_times': db.execute('SELECT count(*) FROM historical_flights WHERE scheduled_departure_time IS NULL OR scheduled_arrival_time IS NULL').fetchone()[0],
            'historical_date_range': list(db.execute('SELECT min(flight_date), max(flight_date) FROM historical_flights').fetchone()),
            'accessibility_passengers': db.execute('SELECT count(*) FROM passengers WHERE accessibility_needs IS NOT NULL').fetchone()[0],
            'inventory_flight_rows': len(flights),
            'accessibility_inventory_positive_rows': sum(f['accessible_slots_available'] > 0 for f in flights),
            'synthetic_names_and_refs': db.execute("SELECT count(*) FROM passengers WHERE display_name LIKE 'Synthetic Passenger %' AND synthetic_ref LIKE 'SYN-P%'").fetchone()[0],
            'audit_classification': audit['data_classification'],
            'indexes': [dict(r) for r in db.execute("SELECT tbl_name, name, sql FROM sqlite_master WHERE type='index' AND tbl_name IN ('flights','historical_flights','source_files')")],
            'foreign_key_violations': [list(r) for r in db.execute('PRAGMA foreign_key_check')],
            'timestamp_caveat': 'BTS local clock values were labelled UTC by the demo seed; stored timestamps have no offset. These are not verified UTC instants.',
        }
        return result


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
