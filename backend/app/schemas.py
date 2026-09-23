"""Pydantic response contracts for the Day 1 API."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class CancelledFlightSummary(BaseModel):
    disruption_id: int
    flight_id: int
    flight_number: str
    origin_code: str
    destination_code: str
    scheduled_departure: datetime
    disruption_type: str
    reason: str

    @field_validator("scheduled_departure")
    @classmethod
    def make_departure_explicitly_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ScenarioSummary(BaseModel):
    fictional_airline: str
    scenario_name: str
    data_notice: str
    airports: int
    flights: int
    passengers: int
    bookings: int
    disruptions: int
    affected_passengers: int
    cancelled_flight: CancelledFlightSummary


class AffectedPassengerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    passenger_id: int
    synthetic_ref: str
    display_name: str
    group_code: str
    cabin: str
    accessibility_needs: str | None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details_json: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def make_created_at_explicitly_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
