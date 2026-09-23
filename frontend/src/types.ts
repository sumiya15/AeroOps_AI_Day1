export interface CancelledFlightSummary {
  disruption_id: number;
  flight_id: number;
  flight_number: string;
  origin_code: string;
  destination_code: string;
  scheduled_departure: string;
  disruption_type: string;
  reason: string;
}

export interface ScenarioSummary {
  fictional_airline: string;
  scenario_name: string;
  data_notice: string;
  airports: number;
  flights: number;
  passengers: number;
  bookings: number;
  disruptions: number;
  affected_passengers: number;
  cancelled_flight: CancelledFlightSummary;
}

export interface AffectedPassenger {
  passenger_id: number;
  synthetic_ref: string;
  display_name: string;
  group_code: string;
  cabin: "ECONOMY" | "BUSINESS";
  accessibility_needs: string | null;
}

