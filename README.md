# AssetFlow

**Enterprise Asset & Resource Management SaaS** — digitizes how organizations track, allocate, and maintain physical assets and shared resources (equipment, furniture, vehicles, rooms) through a centralized, ERP-style platform. Built for offices, schools, hospitals, factories, and agencies.

Covers: organization setup, asset lifecycle tracking, allocation/transfer with conflict handling, resource booking with overlap validation, maintenance approval workflows, structured audit cycles, analytics, and notifications.

Out of scope: purchasing, invoicing, and accounting. (Acquisition Cost is stored for reporting only.)

---

## Tech Stack

> **Note:** This section reflects the stack actually implemented in this repository. It was originally scaffolded with a different intended stack (Bun + Next.js + Prisma) — see [Architecture History](#architecture-history) below.

| Layer          | Technology |
|----------------|------------|
| Frontend       | React (Create React App) |
| Backend        | FastAPI (Python) |
| Database       | MongoDB |
| Package manager (frontend) | Yarn |
| Package manager (backend)  | pip / requirements.txt |
| Scheduled jobs | Custom in-process loop (`scheduler.py`) — see [Known Issues](#known-issues) for the production caveat |
| File uploads   | Handled via `storage.py` |
| Email          | Handled via `emailer.py` |

---

## Project Structure

```
AssetFlow/
├── backend/                     # FastAPI application
│   ├── routers/                 # Route modules, one per domain
│   │   ├── auth.py              # Login/signup, session handling
│   │   ├── org.py               # Organization / department setup
│   │   ├── assets.py            # Asset registration & directory
│   │   ├── allocation.py        # Allocation & transfer workflow
│   │   ├── booking.py           # Resource booking
│   │   ├── maintenance.py       # Maintenance request workflow
│   │   └── audit.py             # Asset audit cycles
│   ├── tests/                   # Backend test suite
│   ├── deps.py                  # Shared dependencies: db client, logger, notification helper
│   ├── storage.py                # Object storage helper (uploads: photos, documents)
│   ├── emailer.py                # Email sending + templated overdue-reminder HTML
│   ├── scheduler.py              # Background job: overdue_reminder_loop
│   ├── seed.py                   # Seeds demo/test data + default role credentials
│   ├── server.py                 # FastAPI app entrypoint — mounts all routers, CORS config
│   ├── requirements.txt          # Python dependencies
│   ├── pytest.ini                # Test configuration
│   └── .env                      # Local environment variables (not committed)
│
├── frontend/                    # React app (Create React App)
│   ├── public/                   # Static assets, index.html
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Screen-level views (Dashboard, Assets, Booking, etc.)
│   │   ├── App.js                # Root component / routing
│   │   └── index.js               # Entry point
│   ├── package.json
│   └── .env                      # Local environment variables (not committed)
│
├── .emergent/                    # Emergent app-builder metadata (build sandbox artifacts)
├── memory/                       # Emergent agent memory/context files
├── test_reports/                 # Generated test run reports
├── tests/                        # Top-level integration/e2e tests
├── design_guidelines.json        # Design tokens / visual language reference
├── test_result.md                # Test run summary log
├── yarn.lock
└── README.md
```

> Frontend structure above follows standard Create React App conventions; verify exact file names against your local checkout if you've customized it.

---

## Core Data Model

The backend is organized around these entities (stored in MongoDB):

- **Organization** — top-level tenant
- **Department** — supports hierarchy via `parentDepartment`
- **AssetCategory** — e.g. Electronics, Furniture, Vehicles
- **Employee/User** — linked to auth identity, department, and role
- **Asset** — lifecycle status: `Available`, `Allocated`, `Reserved`, `Under Maintenance`, `Lost`, `Retired`, `Disposed`
- **Allocation** / **TransferRequest**
- **Resource** / **Booking**
- **MaintenanceRequest**
- **AuditCycle** + **AuditItem**
- **Notification**
- **ActivityLog**

### Roles

Roles are assigned **only** by an Admin via the Employee Directory — never selected at signup.

- **Admin** — manages departments, asset categories, audit cycles, role assignment; org-wide analytics
- **Asset Manager** — registers/allocates assets; approves transfers, maintenance, audit resolutions
- **Department Head** — views/approves within their department; books resources
- **Employee** — views own assets; books resources; raises maintenance requests

### Key Business Rules

- **Double-allocation block**: an already-allocated asset cannot be re-allocated; the API rejects it and surfaces the current holder, offering a Transfer Request instead.
- **Booking overlap validation**: two bookings for the same resource cannot overlap; back-to-back bookings (end = next start) are allowed.
- **Overdue detection**: computed for allocations past their Expected Return Date and bookings/maintenance past expected timelines — feeds the Dashboard and Notifications.

---

## Screens / Features

1. **Login / Signup** — email/password + Google sign-in; signup creates an Employee-only account
2. **Dashboard** — KPI cards, overdue-returns banner, quick actions, recent activity
3. **Organization Setup** (Admin only) — Departments, Asset Categories, Employee Directory (role promotion)
4. **Asset Registration & Directory** — register assets, search/filter, per-asset history
5. **Asset Allocation & Transfer** — allocate, transfer workflow, return flow, overdue flagging
6. **Resource Booking** — calendar/timeline view, conflict validation, cancel/reschedule
7. **Maintenance Management** — request intake, Kanban workflow, auto status sync
8. **Asset Audit** — audit cycles, Verified/Missing/Damaged marking, discrepancy reports
9. **Reports & Analytics** — utilization, maintenance frequency, department summaries, CSV/PDF export
10. **Activity Logs & Notifications** — filterable feed, full audit trail

---

## Prerequisites

- **Python 3.12** (for the backend — confirm against `backend/requirements.txt`)
- **Node.js** + **Yarn** (for the frontend)
- **MongoDB** — local instance or a hosted cluster (e.g. MongoDB Atlas)

---

## Environment Variables

### `backend/.env`

| Variable | Description |
|---|---|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name (if used separately from the connection string) |
| `CORS_ORIGINS` | Allowed frontend origin(s) for CORS |
| SMTP-related vars | Used by `emailer.py` for sending overdue-reminder and notification emails |

### `frontend/.env`

| Variable | Description |
|---|---|
| `REACT_APP_BACKEND_URL` | Base URL the frontend uses to call the backend API |

> Check `deps.py` and `emailer.py` directly for the exact variable names your local `.env` needs — names above are inferred from usage patterns and should be confirmed against source.

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/ayshrosine/AssetFlow.git
cd AssetFlow

# --- Backend ---
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in MONGO_URL, etc.
python seed.py                  # seeds demo data + default credentials
uvicorn server:app --reload     # http://localhost:8000/docs

# --- Frontend (new terminal) ---
cd ../frontend
yarn install
cp .env.example .env            # set REACT_APP_BACKEND_URL=http://localhost:8000
yarn start                      # http://localhost:3000
```

---

## Seeded Demo Credentials

Automatically created by `backend/seed.py` on backend startup (works in both preview and production deployments):

| Role | Email | Password |
|---|---|---|
| Admin | `admin@assetflow.io` | `admin123` |
| Asset Manager | `manager@assetflow.io` | `manager123` |
| Department Head | `head@assetflow.io` | `head123` |
| Employee | `employee@assetflow.io` | `employee123` |

> Change or remove these before any real production launch — they are demo-only credentials.

---

## Deployment (Vercel)

Deployed as **two separate Vercel projects**:

**Backend** — Root Directory: `backend`, framework: FastAPI (Python), entrypoint `server:app`. Set `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, and email vars in Project Settings → Environment Variables.

**Frontend** — Root Directory: `frontend`, Build Command `yarn build`, Output Directory `build`, Install Command `yarn install`. Set `REACT_APP_BACKEND_URL` to the deployed backend's URL.

After deploying, set the backend's `CORS_ORIGINS` to the frontend's live URL and redeploy the backend.

---

## Known Issues

- **`scheduler.py`'s `overdue_reminder_loop`** runs as an in-process background loop, which does not persist on serverless platforms like Vercel (functions don't stay alive between requests). For production, convert this to a scheduled HTTP endpoint triggered by a cron job (e.g. Vercel Cron) instead of an in-process `asyncio` loop.
- **`emergentintegrations` dependency**: `backend/requirements.txt` may reference a package (`emergentintegrations`) that is private to the Emergent build sandbox and unavailable on public PyPI. Replace usages with the underlying library directly (commonly `litellm`) before deploying outside Emergent.

---

## Architecture History

This repository was originally scaffolded against a different intended architecture (Bun package manager, Next.js App Router, Prisma ORM over PostgreSQL, Vercel Blob storage, deployed as a single Next.js app). The version actually implemented here — FastAPI + MongoDB backend with a separately-built React (CRA) frontend — is what's documented above and reflects the real, deployable structure of this repo.

---

## Testing

```bash
cd backend
pytest
```

Test reports are written to `test_reports/`; a running summary is kept in `test_result.md`.
