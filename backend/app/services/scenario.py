"""Build the compact scenario summary used by the operator dashboard."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Airport, Booking, Disruption, Flight, Passenger
from app.schemas import CancelledFlightSummary, ScenarioSummary
from app.services.impact import get_affected_passengers


def get_demo_summary(db: Session) -> ScenarioSummary:
    disruption = db.scalar(
        select(Disruption)
        .options(joinedload(Disruption.flight))
        .order_by(Disruption.id)
        .limit(1)
    )
    if disruption is None:
        raise RuntimeError("Demo scenario is not seeded")

    return ScenarioSummary(
        fictional_airline="AeroNova (fictional)",
        scenario_name="Day 1 DFW cancellation impact scenario",
        data_notice=(
            "Airports and schedule traces come from public datasets. Passenger, "
            "booking, seat inventory, policy and disruption records are synthetic."
        ),
        airports=db.scalar(select(func.count()).select_from(Airport)) or 0,
        flights=db.scalar(select(func.count()).select_from(Flight)) or 0,
        passengers=db.scalar(select(func.count()).select_from(Passenger)) or 0,
        bookings=db.scalar(select(func.count()).select_from(Booking)) or 0,
        disruptions=db.scalar(select(func.count()).select_from(Disruption)) or 0,
        affected_passengers=len(get_affected_passengers(db, disruption)),
        cancelled_flight=CancelledFlightSummary(
            disruption_id=disruption.id,
            flight_id=disruption.flight.id,
            flight_number=disruption.flight.flight_number,
            origin_code=disruption.flight.origin_code,
            destination_code=disruption.flight.destination_code,
            scheduled_departure=disruption.flight.scheduled_departure,
            disruption_type=disruption.disruption_type,
            reason=disruption.reason,
        ),
    )
