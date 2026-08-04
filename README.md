# AssetFlow

**Enterprise Asset & Resource Management SaaS** — digitizes how organizations track, allocate, and maintain physical assets and shared resources (equipment, furniture, vehicles, rooms) through a centralized, ERP-style platform. Built for offices, schools, hospitals, factories, and agencies.

Covers: organization setup, asset lifecycle tracking, allocation/transfer with conflict handling, resource booking with overlap validation, maintenance approval workflows, structured audit cycles, analytics, and notifications.

Out of scope: purchasing, invoicing, and accounting. (Acquisition Cost is stored for reporting only.)

Live On :- https://deploy-launch-10.emergent.host

---

## Tech Stack

> **Note:** This section reflects the stack actually implemented in this repository. It was originally scaffolded with a different intended stack (Bun + Next.js + Prisma) — see [Architecture History](#architecture-history) below.

| Layer          | Technology |
|----------------|------------|
| Frontend       | React (Create React App) |
| Backend        | FastAPI (Python) |
| Database       | MongoDB |
| Package manager (frontend) | npm |
| Package manager (backend)  | pip / requirements.txt |
| Authentication | Email/Password + Google OAuth (@react-oauth/google, google-auth) |
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
│   │   ├── context/              # React Context providers (AuthContext, etc.)
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

1. **Login / Signup** — email/password + Google OAuth sign-in; signup creates an Employee-only account
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

- **Python 3.11+** (for the backend — confirm against `backend/requirements.txt`)
- **Node.js** + **npm** (for the frontend)
- **MongoDB** — local instance or a hosted cluster (e.g. MongoDB Atlas)
- **Google Cloud Console Project** (for Google OAuth - optional but recommended)

---

## Environment Variables

### `backend/.env`

| Variable | Description | Required |
|---|---|---|
| `MONGO_URL` | MongoDB connection string (local or Atlas) | Yes |
| `DB_NAME` | Database name | Yes |
| `JWT_SECRET` | Secret key for JWT token signing | Yes |
| `CORS_ORIGINS` | Allowed frontend origin(s) for CORS (comma-separated) | Yes |
| `FRONTEND_URL` | Frontend URL for CORS and cookie settings | Yes |
| `ENV` | Environment mode (`development` or `production`) | No (defaults to development) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID for Google sign-in | Yes (for Google OAuth) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Yes (for Google OAuth) |
| `ADMIN_EMAIL` | Admin email for seeding demo data | Yes |
| `ADMIN_PASSWORD` | Admin password for seeding demo data | Yes |
| `EMERGENT_LLM_KEY` | API key for LLM integrations (optional) | No |
| `RESEND_API_KEY` | Resend API key for email sending | No |
| `SENDER_EMAIL` | Sender email for Resend | No |
| `APP_NAME` | Application name | No |

### `frontend/.env`

| Variable | Description | Required |
|---|---|---|
| `REACT_APP_BACKEND_URL` | Base URL the frontend uses to call the backend API | Yes |
| `REACT_APP_GOOGLE_CLIENT_ID` | Google OAuth Client ID for Google sign-in | Yes (for Google OAuth) |

### Environment Setup Notes

- **Development Mode**: Set `ENV=development` for local development (uses HTTP cookies)
- **Production Mode**: Set `ENV=production` for production (uses HTTPS cookies)
- **Cookie Security**: Cookie settings automatically adjust based on `ENV` variable
- **Google OAuth**: Requires Google Cloud Console project with OAuth 2.0 Client ID configured

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
# Create .env file with required variables (see Environment Variables section)
# Example backend/.env:
# MONGO_URL=mongodb+srv://your-connection-string
# DB_NAME=assetflow
# JWT_SECRET=your-secret-key
# CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# FRONTEND_URL=http://localhost:3000
# ENV=development
# GOOGLE_CLIENT_ID=your-google-client-id
# GOOGLE_CLIENT_SECRET=your-google-client-secret
# ADMIN_EMAIL=admin@assetflow.io
# ADMIN_PASSWORD=admin123
python seed.py                  # seeds demo data + default credentials
uvicorn server:app --reload --host 0.0.0.0 --port 8000     # http://localhost:8000/docs

# --- Frontend (new terminal) ---
cd ../frontend
npm install
# Create .env file with required variables
# Example frontend/.env:
# REACT_APP_BACKEND_URL=http://localhost:8000
# REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
npm start                      # http://localhost:3000
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

## Recent Changes & Updates

### Google OAuth Integration (2026-08-05)

**What Changed:**
- Implemented direct Google OAuth authentication using `@react-oauth/google` (frontend) and `google-auth` (backend)
- Removed dependency on external OAuth service (auth.emergentagent.com)
- Updated authentication flow to use Google ID token verification on backend
- Modified cookie settings to work with HTTP (development) and HTTPS (production)

**Technical Implementation:**
- **Frontend**: 
  - Added `@react-oauth/google` package for Google OAuth popup flow
  - Replaced external OAuth button with GoogleLogin component
  - Added `googleLogin` function to AuthContext for token handling
  - Removed AuthCallback page (no longer needed)
- **Backend**:
  - Added `google-auth` library for ID token verification
  - Replaced `/api/auth/google/session` endpoint with `/api/auth/google/token`
  - Implemented Google ID token verification using Google Auth Library
  - Updated input models from `GoogleSessionIn` to `GoogleTokenIn`
- **Configuration**:
  - Added `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to backend .env
  - Added `REACT_APP_GOOGLE_CLIENT_ID` to frontend .env
  - Added `ENV` variable for development/production mode switching
  - Updated cookie security settings based on environment

**Authentication Flow:**
1. User clicks "Continue with Google" button
2. Google OAuth popup opens for authentication
3. User authorizes the application
4. Frontend receives Google ID token
5. Frontend sends token to backend `/api/auth/google/token`
6. Backend verifies token with Google Auth Library
7. User is created/updated and logged in
8. User redirected to dashboard

**Benefits:**
- No external OAuth service dependency
- More secure (backend token verification)
- Better user experience (popup flow)
- Works with both development and production environments

### Cookie Security Update (2026-08-05)

**What Changed:**
- Updated cookie settings to work with HTTP (development) and HTTPS (production)
- Added `ENV` environment variable to control cookie security settings
- Modified `set_auth_cookies` and `clear_auth_cookies` functions in deps.py
- Updated refresh token and session token cookie settings in auth.py

**Cookie Configuration:**
- **Development** (`ENV=development`): `secure=False`, `samesite="lax"`
- **Production** (`ENV=production`): `secure=True`, `samesite="none"`

### Database Connection Update (2026-08-05)

**What Changed:**
- Updated MongoDB connection string from local MongoDB to MongoDB Atlas
- Configured `MONGO_URL` with MongoDB Atlas connection string
- Updated backend configuration to use hosted MongoDB database

---

## Known Issues

- **`scheduler.py`'s `overdue_reminder_loop`** runs as an in-process background loop, which does not persist on serverless platforms like Vercel (functions don't stay alive between requests). For production, convert this to a scheduled HTTP endpoint triggered by a cron job (e.g. Vercel Cron) instead of an in-process `asyncio` loop.
- **`emergentintegrations` dependency**: `backend/requirements.txt` may reference a package (`emergentintegrations`) that is private to the Emergent build sandbox and unavailable on public PyPI. Replace usages with the underlying library directly (commonly `litellm`) before deploying outside Emergent.
- **Google OAuth in Development**: Google OAuth requires HTTPS in production but works with HTTP in development mode. Ensure proper environment configuration (`ENV=development` vs `ENV=production`).

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
