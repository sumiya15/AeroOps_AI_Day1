# AeroOps AI

**Explainable Airline Disruption-Recovery Decision-Support Workbench**

AeroOps AI is a full-stack portfolio project demonstrating how an airline operations team could:

- Identify bookings affected by a cancelled flight
- Generate eligible alternative-flight options
- Enforce capacity, cabin, passenger-group, and accessibility constraints
- Rank recovery options deterministically
- Explain recommendations using fictional policy citations
- Allow a human operator to approve or reject a recommendation
- Create synthetic seat holds transactionally
- Produce notification previews
- Record an auditable workflow history

> **Independent educational project:** AeroOps AI uses a fictional airline, synthetic passenger records, fictional operational policies, and historical public flight data. It is not affiliated with Emirates or any other airline. It does not access real bookings, reserve real seats, or send real passenger communications.

## Current Status: Core MVP Complete

The core AeroOps AI MVP is complete.

The project now includes:

- Historical BTS flight data
- Airport metadata from OurAirports
- A deterministic synthetic disruption scenario
- Normalized bookings, passengers, inventory, and accessibility data
- Explainable recovery-option generation
- Constraint enforcement
- Deterministic ranking
- Fictional policy retrieval and exact citations
- Human approval and rejection workflow
- Transactional synthetic seat holds
- Idempotency and capacity-conflict protection
- Notification previews
- Booking and case audit trails
- FastAPI backend
- React operator dashboard
- Automated regression and workflow verification

The original “Day 1” checks remain in the repository as regression tests for the historical-data foundation. They no longer represent the overall project status.

## Demonstration Scenario

The deterministic demonstration contains:

| Item | Value |
|---|---:|
| Historical BTS flights | 196,701 |
| Derived demonstration flights | 20 |
| Synthetic disruption | 1 |
| Synthetic bookings | 24 |
| Synthetic passengers | 50 |
| Recovery alternatives | 2 |
| Fictional policy documents | 5 |

The scenario uses a fictional airline identified as `AO-DEMO`.

A historical BTS row supplies the schedule shape for the demonstration, but the cancellation, bookings, passengers, inventory, policies, recommendations, approvals, seat holds, and notifications are synthetic.

## Operator Dashboard

### Disruption Overview

![AeroOps AI disruption overview](docs/assets/operator-dashboard/01-disruption-overview.png)

### Explainable Recovery Options

![Explainable ranked recovery options](docs/assets/operator-dashboard/02-explainable-options.png)

### Approval, Notification Preview and Audit Trail

![Approved recovery with notification preview and audit trail](docs/assets/operator-dashboard/03-approved-preview-audit.png)


## Main Capabilities

### Disruption and affected-booking detection

The application identifies bookings affected by the synthetic cancelled flight and presents them in the operator dashboard.

### Constraint-aware recovery

Recovery options enforce:

- Whole-party seat availability
- Requested cabin availability
- Passenger-group constraints
- Accessibility requirements
- Alternative-flight capability requirements

An option that violates a hard constraint remains visible but is marked ineligible with explicit reasons.

### Explainable ranking

Eligible alternatives are ranked using a deterministic, illustrative scoring formula.

The same data produces the same ranking. The frontend does not calculate eligibility or ranking; it displays results returned by the backend.

### Policy-grounded explanations

Recovery decisions cite fictional policy documents stored under:

```text
data/policies/fictional/
```

Each citation includes available information such as:

- Policy ID
- Version
- Title
- Section
- Anchor
- Exact excerpt
- Synthetic classification

The policies are fictional and are included only to demonstrate explainable retrieval and evidence-linked decision support.

### Human approval workflow

An operator can:

1. Generate recovery options
2. Review eligible and ineligible alternatives
3. Inspect explanations and policy evidence
4. Approve an eligible option
5. Reject recovery where permitted
6. Review the resulting workflow and audit history

Approval creates a synthetic seat hold for the complete booking party in one transaction.

The workflow includes:

- Idempotent approval handling
- Whole-party capacity protection
- `409 CAPACITY_CONFLICT` handling
- Prevention of partial seat holds
- Terminal approval/rejection states
- Ordered audit events

### Notification preview

A successful approval can produce a synthetic passenger-notification preview.

> **Preview only — not sent.**

The application does not connect to email, SMS, airline reservation, or passenger-service systems.

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest

### Frontend

- React
- TypeScript
- Vite

### Data

- BTS Reporting Carrier On-Time Performance data
- OurAirports airport and country metadata
- Deterministic synthetic operational fixtures
- Fictional policy documents

## Project Structure

```text
AeroOps_AI_Day1/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
│   └── src/
├── data/
│   ├── demo/
│   ├── policies/
│   │   └── fictional/
│   ├── raw/
│   └── processed/
├── docs/
└── README.md
```

Generated databases, downloaded source files, command transcripts, and temporary verification artifacts are excluded from Git where appropriate.

## Run the Application on Windows

Open PowerShell in the repository root.

### 1. Install backend dependencies

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1
python -m pip install -r backend\requirements.txt
```

### 2. Start the backend

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///C:/Users/sumiy/Documents/sumiya/OneDrive/Desktop/AeroOps_AI_Day1/data/processed/aeroops_day1.sqlite"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Start the frontend

Open a second PowerShell terminal:

```powershell
cd C:\Users\sumiy\Documents\sumiya\OneDrive\Desktop\AeroOps_AI_Day1\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### 4. Open the application

- Operator dashboard: `http://localhost:5173`
- FastAPI documentation: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`

## Demonstration Flow

1. Open the operator dashboard.
2. Select the AO-DEMO disruption.
3. Select an affected synthetic booking.
4. Generate recovery options.
5. Compare eligible and ineligible alternatives.
6. Review rankings, constraints, explanations, and citations.
7. Approve an eligible option or reject the recovery.
8. Review the resulting workflow state.
9. Inspect the notification preview.
10. Inspect the booking audit timeline.

Use the isolated verification workflow when testing mutations so the development database is not unintentionally changed.

## API Overview

### General endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/v1/demo/summary` | Demonstration-data summary |
| POST | `/api/v1/demo/reset` | Restore local deterministic demo data |
| GET | `/api/v1/disruptions/{id}/affected-passengers` | Retrieve affected synthetic passengers |
| GET | `/api/v1/audit-logs` | Retrieve general scenario audit records |

### Recovery endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/recovery/cases` | List recovery cases |
| GET | `/api/v1/recovery/cases/{disruption_id}/bookings` | List affected bookings |
| GET | `/api/v1/recovery/bookings/{booking_id}/options` | Retrieve recovery options |
| POST | `/api/v1/recovery/bookings/{booking_id}/options/generate` | Generate deterministic options |
| POST | `/api/v1/recovery/bookings/{booking_id}/approve` | Approve an eligible option |
| POST | `/api/v1/recovery/bookings/{booking_id}/reject` | Reject recovery |
| GET | `/api/v1/recovery/bookings/{booking_id}/workflow` | Retrieve workflow state |
| GET | `/api/v1/recovery/bookings/{booking_id}/notification-preview` | Retrieve notification preview |
| GET | `/api/v1/recovery/bookings/{booking_id}/audit` | Retrieve booking audit history |
| GET | `/api/v1/recovery/cases/{disruption_id}/audit` | Retrieve case audit history |

Policy search and citation-resolution endpoints are also available in the generated FastAPI documentation.

## Verification

The verified core MVP results include:

| Check | Result |
|---|---:|
| Backend test suite | 185 passed |
| Focused transactional-workflow tests | 36 passed |
| Frontend TypeScript/production build | Passed |
| Day 1 validation | 13 passed |
| Recovery verification | 5/5 passed |
| Policy verification | 7/7 passed |
| Isolated workflow verification | 10/10 passed |
| Foreign-key integrity | Passed |
| Git whitespace check | Passed |

The isolated workflow verified:

- Complete-party seat holds
- Idempotent repeated approval
- No duplicate hold creation
- Capacity-conflict responses
- No partial inventory mutation
- Rejection without seat holds
- Rejection without notification previews
- Deterministic audit-event ordering

Run the isolated workflow verification from the backend directory:

```powershell
cd backend
python -m app.verify_workflow
```

This uses a temporary database and does not approve bookings in the development database.

## Data Provenance

The public-data foundation uses:

- OurAirports `airports.csv`
- OurAirports `countries.csv`
- BTS Reporting Carrier On-Time Performance data for January 2025

Source metadata and cryptographic hashes are recorded for reproducibility.

Historical public data remains separate from the synthetic operational demonstration.

Detailed verification is available in:

- [`docs/DAY1_VERIFICATION.md`](docs/DAY1_VERIFICATION.md)
- [`docs/SYNTHETIC_DOMAIN.md`](docs/SYNTHETIC_DOMAIN.md)
- [`docs/RECOVERY_ENGINE.md`](docs/RECOVERY_ENGINE.md)
- [`docs/RECOVERY_API.md`](docs/RECOVERY_API.md)
- [`docs/FICTIONAL_POLICIES.md`](docs/FICTIONAL_POLICIES.md)
- [`docs/RECOVERY_WORKFLOW.md`](docs/RECOVERY_WORKFLOW.md)
- [`docs/OPERATOR_DASHBOARD.md`](docs/OPERATOR_DASHBOARD.md)
- [`docs/FINAL_VERIFICATION.md`](docs/FINAL_VERIFICATION.md)

## Safety and Data Classification

| Data type | Classification |
|---|---|
| BTS flight records | Historical public data |
| OurAirports metadata | Public airport metadata |
| Demonstration flights | Derived demonstration data |
| Disruption event | Synthetic |
| Bookings and passengers | Synthetic |
| Seat inventory and holds | Synthetic |
| Accessibility requirements | Synthetic |
| Policy documents | Fictional |
| Recovery recommendations | Synthetic decision-support output |
| Notification messages | Preview only; not sent |

## Important Limitations

- This is a decision-support demonstration, not a production airline system.
- It does not connect to real airline reservation or departure-control systems.
- It does not contain real passenger bookings or personally identifiable information.
- It does not provide real-time flight status or weather.
- It does not reserve real seats or issue tickets.
- It does not send email, SMS, or push notifications.
- The ranking formula is deterministic and illustrative, not machine-learned.
- The policies are fictional and do not represent any airline’s internal rules.
- Accessibility capabilities are simplified for demonstration purposes.
- The local reset and transactional endpoints are unauthenticated and must not be exposed publicly without additional security.
- SQLite is appropriate for this local MVP but not for a production airline workflow.
- Recommendations and notification previews must be reviewed by a human operator.

## Project Purpose

AeroOps AI demonstrates practical experience with:

- Full-stack application development
- REST API design
- Relational data modelling
- Deterministic decision systems
- Explainable recommendations
- Constraint validation
- Transaction management
- Idempotency
- Audit logging
- Policy-grounded citations
- Human-in-the-loop workflows
- Synthetic-data safety
- Automated testing and reproducible verification

## Licence and Attribution

Public datasets remain subject to their respective source terms.

This repository’s synthetic fixtures, fictional policies, application code, and documentation are provided for educational and portfolio demonstration purposes.
