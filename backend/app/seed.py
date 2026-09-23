"""Create a deterministic synthetic demonstration scenario."""

from datetime import datetime, time, timedelta, timezone
import json

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    Airport,
    AuditLog,
    Booking,
    BookingStatus,
    Cabin,
    Disruption,
    Flight,
    FlightStatus,
    HistoricalFlight,
    Passenger,
    PublicAirport,
)


FOCUS_AIRPORTS = ["JFK", "ATL", "ORD", "DFW", "LAX", "SFO"]

FALLBACK_AIRPORTS = [
    ("JFK", "John F Kennedy International Airport", "New York"),
    ("ATL", "Hartsfield Jackson Atlanta International Airport", "Atlanta"),
    ("ORD", "Chicago O'Hare International Airport", "Chicago"),
    ("DFW", "Dallas Fort Worth International Airport", "Dallas-Fort Worth"),
    ("LAX", "Los Angeles International Airport", "Los Angeles"),
    ("SFO", "San Francisco International Airport", "San Francisco"),
]


FALLBACK_FLIGHT_ROUTES = [
    ("ANV101", "DFW", "LAX", 8, 3, FlightStatus.CANCELLED.value, 0, 0, 0),
    ("ANV103", "DFW", "LAX", 15, 3, FlightStatus.SCHEDULED.value, 7, 2, 1),
    ("ANV105", "DFW", "SFO", 30, 3, FlightStatus.SCHEDULED.value, 8, 1, 2),
    ("ANV107", "DFW", "JFK", 9, 3, FlightStatus.SCHEDULED.value, 9, 2, 2),
    ("ANV109", "DFW", "ATL", 11, 2, FlightStatus.SCHEDULED.value, 6, 2, 1),
    ("ANV111", "LAX", "DFW", 13, 3, FlightStatus.SCHEDULED.value, 10, 3, 2),
    ("ANV113", "SFO", "DFW", 14, 3, FlightStatus.SCHEDULED.value, 5, 1, 1),
    ("ANV115", "JFK", "DFW", 16, 4, FlightStatus.SCHEDULED.value, 11, 2, 2),
    ("ANV117", "DFW", "ORD", 7, 2, FlightStatus.SCHEDULED.value, 12, 3, 2),
    ("ANV119", "ORD", "DFW", 10, 2, FlightStatus.SCHEDULED.value, 8, 2, 1),
    ("ANV121", "ATL", "DFW", 6, 2, FlightStatus.SCHEDULED.value, 14, 4, 3),
    ("ANV123", "DFW", "ATL", 12, 2, FlightStatus.SCHEDULED.value, 9, 3, 2),
    ("ANV125", "LAX", "SFO", 17, 1, FlightStatus.SCHEDULED.value, 7, 1, 1),
    ("ANV127", "SFO", "LAX", 19, 1, FlightStatus.SCHEDULED.value, 7, 1, 1),
    ("ANV129", "ATL", "JFK", 20, 2, FlightStatus.SCHEDULED.value, 10, 2, 2),
    ("ANV131", "JFK", "ATL", 22, 2, FlightStatus.SCHEDULED.value, 10, 2, 2),
    ("ANV133", "ORD", "JFK", 23, 2, FlightStatus.SCHEDULED.value, 5, 1, 1),
    ("ANV135", "JFK", "ORD", 26, 2, FlightStatus.SCHEDULED.value, 5, 1, 1),
    ("ANV137", "SFO", "ORD", 28, 4, FlightStatus.SCHEDULED.value, 8, 2, 1),
    ("ANV139", "ORD", "SFO", 32, 4, FlightStatus.SCHEDULED.value, 8, 2, 1),
]


def _group_for_passenger(number: int) -> str:
    if number <= 3:
        return "GRP-001"
    if number <= 5:
        return "GRP-002"
    if number <= 9:
        return "GRP-003"
    if number <= 11:
        return "GRP-004"
    if number == 12:
        return "GRP-005"
    return f"GRP-{((number - 13) // 2) + 6:03d}"


def _public_airports(db: Session) -> list[tuple[str, str, str]]:
    rows = (
        db.query(PublicAirport)
        .filter(PublicAirport.iata_code.in_(FOCUS_AIRPORTS))
        .order_by(PublicAirport.iata_code)
        .all()
    )
    if len(rows) != 6:
        return FALLBACK_AIRPORTS
    return [
        (row.iata_code, row.name, row.municipality or row.iata_code)
        for row in rows
    ]


def _combine_date_time(source: HistoricalFlight, scheduled_time: time | None) -> datetime:
    if scheduled_time is None:
        scheduled_time = time(12, 0)
    return datetime.combine(source.flight_date, scheduled_time, tzinfo=timezone.utc)


def _historical_routes(db: Session) -> list[tuple]:
    rows = (
        db.query(HistoricalFlight)
        .filter(
            (
                (HistoricalFlight.origin_code == "DFW")
                & (HistoricalFlight.destination_code.in_(FOCUS_AIRPORTS))
            )
            | (
                (HistoricalFlight.destination_code == "DFW")
                & (HistoricalFlight.origin_code.in_(FOCUS_AIRPORTS))
            )
        )
        .order_by(
            HistoricalFlight.cancelled.asc(),
            HistoricalFlight.flight_date.asc(),
            HistoricalFlight.scheduled_departure_time.asc(),
            HistoricalFlight.id.asc(),
        )
        .limit(20)
        .all()
    )
    if len(rows) < 20:
        return FALLBACK_FLIGHT_ROUTES

    routes = []
    for index, row in enumerate(rows, start=1):
        status = (
            FlightStatus.CANCELLED.value
            if index == 1
            else FlightStatus.SCHEDULED.value
        )
        available_economy = 0 if index == 1 else 5 + (index % 10)
        available_business = 0 if index == 1 else 1 + (index % 4)
        accessible_slots = 0 if index == 1 else index % 3
        departure = _combine_date_time(row, row.scheduled_departure_time)
        arrival = _combine_date_time(row, row.scheduled_arrival_time)
        if arrival <= departure:
            arrival = departure + timedelta(hours=2)
        routes.append(
            (
                f"ANV{100 + index:03d}",
                row.origin_code,
                row.destination_code,
                departure,
                arrival,
                status,
                available_economy,
                available_business,
                accessible_slots,
                row,
            )
        )
    return routes


def seed_demo_data(db: Session) -> None:
    """Reset and seed exactly 6 airports, 20 flights and 50 synthetic passengers."""

    for model in (AuditLog, Disruption, Booking, Passenger, Flight, Airport):
        db.execute(delete(model))
    db.flush()

    db.add_all(
        [Airport(code=code, name=name, city=city) for code, name, city in _public_airports(db)]
    )

    base_time = datetime(2027, 1, 15, 0, 0, tzinfo=timezone.utc)
    route_rows = _historical_routes(db)
    flights: list[Flight] = []
    historical_trace_rows = []
    for index, route in enumerate(route_rows, start=1):
        if len(route) == 10:
            (
                flight_number,
                origin,
                destination,
                departure,
                arrival,
                status,
                available_economy,
                available_business,
                accessible_slots,
                historical_row,
            ) = route
            historical_trace_rows.append(
                {
                    "synthetic_flight_id": index,
                    "synthetic_flight_number": flight_number,
                    "bts_source_row_number": historical_row.source_row_number,
                    "bts_reporting_airline": historical_row.reporting_airline,
                    "bts_flight_number": historical_row.flight_number,
                    "bts_origin": historical_row.origin_code,
                    "bts_destination": historical_row.destination_code,
                    "bts_flight_date": historical_row.flight_date.isoformat(),
                    "bts_cancelled": historical_row.cancelled,
                }
            )
        else:
            (
                flight_number,
                origin,
                destination,
                departure_hour,
                duration_hours,
                status,
                available_economy,
                available_business,
                accessible_slots,
            ) = route
            departure = base_time + timedelta(hours=departure_hour)
            arrival = departure + timedelta(hours=duration_hours)

        flights.append(
            Flight(
                id=index,
                flight_number=flight_number,
                origin_code=origin,
                destination_code=destination,
                scheduled_departure=departure,
                scheduled_arrival=arrival,
                status=status,
                capacity_economy=120,
                capacity_business=16,
                available_economy=available_economy,
                available_business=available_business,
                accessible_slots_available=accessible_slots,
            )
        )
    db.add_all(flights)

    passengers: list[Passenger] = []
    bookings: list[Booking] = []
    for number in range(1, 51):
        passenger = Passenger(
            id=number,
            synthetic_ref=f"SYN-P{number:03d}",
            display_name=f"Synthetic Passenger {number:03d}",
            group_code=_group_for_passenger(number),
            accessibility_needs=(
                "WHEELCHAIR_ASSISTANCE"
                if number == 4
                else "HEARING_ASSISTANCE"
                if number == 12
                else None
            ),
        )
        passengers.append(passenger)

        if number <= 12:
            flight_id = 1
            cabin = Cabin.BUSINESS.value if number in {10, 11} else Cabin.ECONOMY.value
        else:
            flight_id = 4 + ((number - 13) % 17)
            cabin = Cabin.BUSINESS.value if number % 13 == 0 else Cabin.ECONOMY.value

        bookings.append(
            Booking(
                passenger_id=number,
                flight_id=flight_id,
                cabin=cabin,
                status=BookingStatus.CONFIRMED.value,
            )
        )

    db.add_all(passengers)
    db.add_all(bookings)
    db.add(
        Disruption(
            id=1,
            flight_id=1,
            disruption_type="CANCELLATION",
            reason=(
                "Synthetic DFW-centered operational cancellation for portfolio "
                "demonstration. It does not claim the source BTS flight was cancelled."
            ),
        )
    )
    db.add(
        AuditLog(
            actor="SYSTEM",
            action="DEMO_SCENARIO_RESET",
            entity_type="SCENARIO",
            entity_id="DAY1-DEMO",
            details_json=json.dumps(
                {
                    "data_classification": "SYNTHETIC",
                    "public_schedule_basis": (
                        "BTS rows are used only as traceable schedule shapes; "
                        "bookings, passengers, inventory, policies and disruption "
                        "are synthetic."
                    ),
                    "historical_trace_rows": historical_trace_rows[:20],
                    "airports": 6,
                    "flights": 20,
                    "passengers": 50,
                    "disruptions": 1,
                },
                sort_keys=True,
            ),
        )
    )
    db.commit()


if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_demo_data(session)
    print("Seeded AeroOps Day 1 DFW demo: 6 airports, 20 flights, 50 passengers.")
