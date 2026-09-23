import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getAffectedPassengers,
  getScenarioSummary,
  resetDemo,
} from "./api";
import type { AffectedPassenger, ScenarioSummary } from "./types";

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function App() {
  const [summary, setSummary] = useState<ScenarioSummary | null>(null);
  const [passengers, setPassengers] = useState<AffectedPassenger[]>([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadScenario = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const nextSummary = await getScenarioSummary();
      const nextPassengers = await getAffectedPassengers(
        nextSummary.cancelled_flight.disruption_id,
      );
      setSummary(nextSummary);
      setPassengers(nextPassengers);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadScenario();
  }, [loadScenario]);

  const affectedGroups = useMemo(
    () => new Set(passengers.map((passenger) => passenger.group_code)).size,
    [passengers],
  );

  async function handleReset() {
    setResetting(true);
    setError(null);
    try {
      await resetDemo();
      await loadScenario();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown error");
    } finally {
      setResetting(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            AO
          </span>
          <div>
            <p className="eyebrow">Operations decision support</p>
            <h1>AeroOps AI</h1>
          </div>
        </div>
        <div className="status-chip">
          <span className="status-dot" aria-hidden="true" /> Day 1 demo
        </div>
      </header>

      <section className="notice" aria-label="Data notice">
        <strong>Synthetic demonstration data.</strong> No real passenger data,
        airline integration or airline affiliation.
      </section>

      {loading ? (
        <section className="state-card" aria-live="polite">
          Loading operational scenario…
        </section>
      ) : error ? (
        <section className="state-card error" role="alert">
          <h2>The dashboard could not load</h2>
          <p>{error}</p>
          <p>Confirm that FastAPI is running on port 8000.</p>
          <button type="button" onClick={() => void loadScenario()}>
            Try again
          </button>
        </section>
      ) : summary ? (
        <>
          <section className="hero-grid">
            <article className="scenario-card">
              <p className="eyebrow">Active disruption</p>
              <div className="route-row">
                <div>
                  <span className="airport-code">
                    {summary.cancelled_flight.origin_code}
                  </span>
                  <span className="route-label">Origin</span>
                </div>
                <div className="route-line" aria-hidden="true">
                  <span />
                  <b>×</b>
                  <span />
                </div>
                <div>
                  <span className="airport-code">
                    {summary.cancelled_flight.destination_code}
                  </span>
                  <span className="route-label">Destination</span>
                </div>
              </div>
              <div className="flight-meta">
                <span>{summary.cancelled_flight.flight_number}</span>
                <span>
                  {formatDateTime(
                    summary.cancelled_flight.scheduled_departure,
                  )}{" "}
                  UTC
                </span>
                <span className="cancelled-badge">Cancelled</span>
              </div>
              <p className="reason">{summary.cancelled_flight.reason}</p>
            </article>

            <article className="metrics-card">
              <div>
                <span>{summary.affected_passengers}</span>
                <p>Affected passengers</p>
              </div>
              <div>
                <span>{affectedGroups}</span>
                <p>Passenger groups</p>
              </div>
              <div>
                <span>{summary.flights}</span>
                <p>Scenario flights</p>
              </div>
              <div>
                <span>{summary.airports}</span>
                <p>Airports</p>
              </div>
            </article>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Impact detection</p>
                <h2>Affected passenger manifest</h2>
              </div>
              <button
                className="secondary-button"
                type="button"
                disabled={resetting}
                onClick={() => void handleReset()}
              >
                {resetting ? "Resetting…" : "Reset synthetic demo"}
              </button>
            </div>

            {passengers.length === 0 ? (
              <div className="empty-state">No affected passengers found.</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Reference</th>
                      <th>Passenger</th>
                      <th>Group</th>
                      <th>Cabin</th>
                      <th>Accessibility requirement</th>
                    </tr>
                  </thead>
                  <tbody>
                    {passengers.map((passenger) => (
                      <tr key={passenger.passenger_id}>
                        <td className="mono">{passenger.synthetic_ref}</td>
                        <td>{passenger.display_name}</td>
                        <td>{passenger.group_code}</td>
                        <td>
                          <span className={`cabin ${passenger.cabin.toLowerCase()}`}>
                            {passenger.cabin}
                          </span>
                        </td>
                        <td>
                          {passenger.accessibility_needs ? (
                            <span className="assistance">
                              {passenger.accessibility_needs.split("_").join(" ")}
                            </span>
                          ) : (
                            <span className="muted">None recorded</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="next-step">
            <span>Next milestone</span>
            <div>
              <h2>Explainable recovery recommendations</h2>
              <p>
                Day 2 will enforce capacity, cabin, accessibility and group
                constraints before ranking direct alternatives within 24 hours.
              </p>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}

export default App;
