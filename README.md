# RCM-Analytics-API
source .venv/bin/activate

# RCM Analytics API

![CI](https://github.com/luis8choa/RCM-Analytics-API/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A production-ready REST API for Healthcare Revenue Cycle Management (RCM) analytics, built with FastAPI and PostgreSQL. Exposes KPIs used daily by billing teams, collectors, and operations managers in U.S. healthcare organizations.

---

## Why This Project

Revenue Cycle Management is the financial backbone of U.S. healthcare. Every claim submitted to a payer (insurance company) goes through a complex cycle — submission, review, payment or denial, appeal. Tracking this cycle efficiently determines whether a healthcare organization gets paid on time or loses revenue to preventable denials.

This API was built by a biomedical engineer working as an HR data analyst in an RCM services company, bridging domain expertise with backend development skills.

---

## Features

- **Denial Rate Analytics** — track claim denial rates by payer, CPT code, and time period
- **AR Days Tracking** — calculate Days in Accounts Receivable with industry benchmarks
- **Aging Buckets** — classify unpaid claims by 0-30, 31-60, 61-90, and 90+ days
- **Staff Productivity** — measure billing staff performance vs team averages
- **Error Rate Monitoring** — identify staff members with high error rates for coaching
- **Configurable Alerts** — webhook notifications when KPIs exceed thresholds
- **JWT Authentication** — secure token-based access control
- **Auto-generated Docs** — interactive Swagger UI at `/docs`

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Client                      │
│         Postman / Browser / App              │
└──────────────────────┬──────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────┐
│              FastAPI Application             │
│  ┌─────────┐ ┌────────┐ ┌────────────────┐  │
│  │ routers │ │schemas │ │ auth (JWT)     │  │
│  └────┬────┘ └────────┘ └────────────────┘  │
│  ┌────▼──────────────────────────────────┐  │
│  │              services                  │  │
│  │  claims · ar · staff · alerts         │  │
│  └────┬──────────────────────────────────┘  │
│  ┌────▼──────────────────────────────────┐  │
│  │         SQLAlchemy ORM + Alembic      │  │
│  └────┬──────────────────────────────────┘  │
└───────┼─────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────┐
│            PostgreSQL 16                     │
│  staff · claims · staff_activity · alerts   │
└─────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt |
| HTTP Client | httpx |
| Testing | pytest + pytest-cov |
| Package Manager | uv |
| Containerization | Docker |
| CI | GitHub Actions |

---

## API Endpoints

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new staff member |
| POST | `/auth/token` | Obtain JWT access token |

### Claims Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/claims` | List claims with filters |
| GET | `/claims/{id}` | Get claim by ID |
| POST | `/claims` | Create a new claim |
| GET | `/claims/denial-rate` | Denial rate by payer and period |
| GET | `/claims/trends` | Weekly claim volume and denial trends |

### AR Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ar/days` | Average Days in AR with benchmark |
| GET | `/ar/aging-buckets` | Unpaid claims by aging bucket |
| GET | `/ar/by-department` | AR days broken down by department |

### Staff Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/staff/productivity` | Claims processed per staff member |
| GET | `/staff/error-rate` | Error rate per staff member |
| GET | `/staff/workload` | Current pending claims per staff member |

### Alerts
| Method | Path | Description |
|--------|------|-------------|
| GET | `/alerts` | List active alert configurations |
| POST | `/alerts/configure` | Create a new alert |
| DELETE | `/alerts/{id}` | Deactivate an alert |
| POST | `/alerts/evaluate` | Manually trigger alert evaluation |

---

## Running Locally

**Prerequisites:** Python 3.11+, Docker, uv

```bash
# 1. Clone the repository
git clone https://github.com/luis8choa/RCM-Analytics-API.git
cd RCM-Analytics-API

# 2. Install dependencies
uv sync --extra dev

# 3. Start PostgreSQL
docker compose up -d

# 4. Configure environment
cp .env.example .env
# Edit .env with your values

# 5. Run migrations
uv run alembic upgrade head

# 6. Seed sample data
uv run python seed.py

# 7. Start the API
uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Running Tests

```bash
# Run all tests with coverage
uv run pytest -v

# Run a specific module
uv run pytest tests/test_claims.py -v

# Generate HTML coverage report
uv run pytest --cov-report=html
open htmlcov/index.html
```

---

## Project Structure

```
RCM-Analytics-API/
├── app/
│   ├── main.py           # FastAPI app, middleware, error handlers
│   ├── config.py         # Settings via pydantic-settings
│   ├── database.py       # SQLAlchemy engine, session, get_db
│   ├── models.py         # ORM models (Staff, Claim, StaffActivity, AlertConfig)
│   ├── auth.py           # JWT creation and verification
│   ├── schemas.py        # Pydantic v2 schemas
│   ├── routers/          # FastAPI routers by domain
│   └── services/         # Business logic layer
├── alembic/              # Database migrations
├── tests/
│   ├── conftest.py       # Shared fixtures, SQLite test DB
│   └── test_*.py         # Test modules by domain
├── seed.py               # Synthetic RCM data generator
├── docker-compose.yml    # PostgreSQL local setup
├── Dockerfile            # Production image
├── render.yaml           # Render deployment config
└── pyproject.toml        # Dependencies and tool config
```

---

## Key Design Decisions

**Service layer pattern** — business logic lives in `services/`, completely separate from HTTP routing. This makes the logic testable without HTTP overhead and reusable across endpoints. The alerts module calls `claims_service` and `ar_service` directly without making internal HTTP requests.

**Soft deletes on alerts** — alert configurations are deactivated (`is_active=False`) rather than deleted, preserving audit history of what thresholds were configured and when.

**SQLite for tests, PostgreSQL for production** — tests run against SQLite for speed and simplicity, with dialect-aware query helpers for date arithmetic that differs between engines.

**Synthetic seed data** — 500+ realistic claims with real CPT codes, fictional payers, and statistically distributed statuses (50% paid, 25% denied, 15% pending, 10% appealed) to produce meaningful KPI calculations.

---

## Domain Context

| Term | Definition |
|------|-----------|
| Claim | Invoice submitted by a provider to an insurance payer |
| CPT Code | Standardized procedure code (e.g. 99213 = office visit) |
| Payer | Insurance company responsible for payment |
| Denial Rate | % of claims rejected by the payer |
| AR Days | Average days from claim submission to payment |
| Aging Bucket | Classification of unpaid claims by days outstanding |

---

## Author

**Luis Ochoa** — Biomedical Engineer · HR Data Analyst · Backend Developer

[LinkedIn](https://linkedin.com/in/luisochoad/) · [GitHub](https://github.com/luis8choa)