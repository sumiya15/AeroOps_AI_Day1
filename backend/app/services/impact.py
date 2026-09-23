"""Queries that identify passengers affected by a disruption."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Disruption, Passenger
from app.schemas import AffectedPassengerOut


def get_affected_passengers(
    db: Session, disruption: Disruption
) -> list[AffectedPassengerOut]:
    rows = db.execute(
        select(Passenger, Booking.cabin)
        .join(Booking, Booking.passenger_id == Passenger.id)
        .where(
            Booking.flight_id == disruption.flight_id,
            Booking.status == BookingStatus.CONFIRMED.value,
        )
        .order_by(Passenger.group_code, Passenger.synthetic_ref)
    ).all()

    return [
        AffectedPassengerOut(
            passenger_id=passenger.id,
            synthetic_ref=passenger.synthetic_ref,
            display_name=passenger.display_name,
            group_code=passenger.group_code,
            cabin=cabin,
            accessibility_needs=passenger.accessibility_needs,
        )
        for passenger, cabin in rows
    ]

