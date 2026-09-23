"""Persistence models for public Day 1 data and the synthetic demo scenario."""

from datetime import date, datetime, time, timezone
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FlightStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"


class Cabin(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Airport(Base):
    __tablename__ = "airports"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_number: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    origin_code: Mapped[str] = mapped_column(ForeignKey("airports.code"), index=True)
    destination_code: Mapped[str] = mapped_column(ForeignKey("airports.code"), index=True)
    scheduled_departure: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scheduled_arrival: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default=FlightStatus.SCHEDULED.value)
    capacity_economy: Mapped[int] = mapped_column(Integer)
    capacity_business: Mapped[int] = mapped_column(Integer)
    available_economy: Mapped[int] = mapped_column(Integer)
    available_business: Mapped[int] = mapped_column(Integer)
    accessible_slots_available: Mapped[int] = mapped_column(Integer, default=0)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="flight")
    disruptions: Mapped[list["Disruption"]] = relationship(back_populates="flight")


class Passenger(Base):
    __tablename__ = "passengers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    synthetic_ref: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    group_code: Mapped[str] = mapped_column(String(20), index=True)
    accessibility_needs: Mapped[str | None] = mapped_column(String(40), nullable=True)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="passenger")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("passengers.id"), index=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), index=True)
    cabin: Mapped[str] = mapped_column(String(20), default=Cabin.ECONOMY.value)
    status: Mapped[str] = mapped_column(
        String(20), default=BookingStatus.CONFIRMED.value
    )

    passenger: Mapped[Passenger] = relationship(back_populates="bookings")
    flight: Mapped[Flight] = relationship(back_populates="bookings")


class Disruption(Base):
    __tablename__ = "disruptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), index=True)
    disruption_type: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    flight: Mapped[Flight] = relationship(back_populates="disruptions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(50))
    details_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(80), index=True)
    origin_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    local_path: Mapped[str] = mapped_column(String(500), unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    file_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieval_note: Mapped[str] = mapped_column(String(300))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PublicAirport(Base):
    __tablename__ = "public_airports"

    iata_code: Mapped[str] = mapped_column(String(3), primary_key=True)
    ident: Mapped[str] = mapped_column(String(12), nullable=False)
    airport_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    municipality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iso_country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    iso_region: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"), index=True)


class HistoricalFlight(Base):
    __tablename__ = "historical_flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"), index=True)
    flight_date: Mapped[date] = mapped_column(Date, index=True)
    reporting_airline: Mapped[str] = mapped_column(String(10), index=True)
    flight_number: Mapped[str] = mapped_column(String(12), index=True)
    origin_code: Mapped[str] = mapped_column(String(3), index=True)
    destination_code: Mapped[str] = mapped_column(String(3), index=True)
    scheduled_departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    scheduled_arrival_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    actual_departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    actual_arrival_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    departure_delay_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    arrival_delay_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    cancellation_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    diverted: Mapped[bool] = mapped_column(Boolean, default=False)
    distance_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_row_number: Mapped[int] = mapped_column(Integer, index=True)
    source_record_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    details_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
