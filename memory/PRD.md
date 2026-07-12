# AssetFlow — PRD & Build Log

## Original Problem Statement
Enterprise Asset & Resource Management Web App (React + FastAPI + MongoDB). Centralized ERP for tracking, allocating, booking, maintaining, and auditing physical assets. Excludes purchasing, invoicing, accounting.

## Architecture (as of iteration 4)

### Backend — modular `routers/*.py`
```
/app/backend/
├── server.py          # Thin bootstrap: mounts /api, CORS, startup (seed, storage, scheduler)
├── deps.py            # Shared: db, JWT/bcrypt helpers, get_current_user, require_roles, all Pydantic models
├── seed.py            # Idempotent seed_data() for demo users, depts, categories, assets
├── storage.py         # Emergent object storage put/get + path builder
├── emailer.py         # Resend email (async via asyncio.to_thread)
├── scheduler.py       # Background overdue-reminder loop with per-day dedupe
└── routers/
    ├── auth.py        # register, login, logout, me, refresh, forgot/reset, Google OAuth session
    ├── org.py         # users, departments, categories, promote
    ├── assets.py      # CRUD + search + detail with allocation/maintenance history
    ├── allocation.py  # allocate (with double-alloc guard), return, transfer (request/approve/reject)
    ├── booking.py     # book (with overlap guard), cancel
    ├── maintenance.py # create + Kanban move (auto asset-status sync)
    ├── audit.py       # cycles: create, list, get, mark item, close (with mutations)
    ├── uploads.py     # multipart upload + short-lived HMAC-signed URLs
    └── dashboard.py   # stats, activity, notifications, manual overdue trigger, health
```

### Frontend — React 19 + Tailwind + shadcn/ui
- Dark theme, Cabinet Grotesk + Satoshi via Fontshare
- AuthProvider (JWT httpOnly cookies + Emergent Google OAuth session cookies)
- FileUploader + AuthedImage (cookie-authed fetch → blob URL)
- Persistent left sidebar, top bar with global search
- 10 screens (Login, Dashboard, Org Setup, Assets, Asset Detail, Allocation & Transfer, Booking, Maintenance Kanban, Audit, Reports, Notifications)

## Security & Access
- JWT httpOnly cookies (SameSite=None, Secure) + bcrypt passwords
- Brute-force lockout: 5 attempts / 15 min, keyed by email (ingress-safe)
- RBAC middleware on every mutating route
- File downloads: httpOnly cookie OR short-lived HMAC-signed URL (5 min TTL, base64url `<exp>.<sig>`) — old `?auth=<jwt>` query param removed

## Integrations
- **Emergent Google OAuth** — coexists with JWT login, unified user store
- **Emergent-managed object storage** — via `storage.py`, 10 MB / file, MIME whitelist
- **Resend email** — overdue-return reminders (best-effort, non-blocking)

## Testing
| Iteration | Focus | Result |
|-----------|-------|--------|
| 1 | Base MVP (phases 1–5) | 18/19 backend, all FE — fixed brute-force + CORS |
| 2 | Uploads, audit, PDF, email | All new BE passed; FE flagged missing FileUploader render |
| 3 | Retest of FileUploader fix | **All clean** |
| 4 | Signed URLs + router split | **16/16 backend, all FE — zero issues** |

## Seed Credentials
See `/app/memory/test_credentials.md`.

## Backlog
- **P3** — Booking recurring/reschedule flow
- **P3** — SMS reminders via Twilio
- **P3** — Public asset "trust page" via QR code (contractors/students scan → view + report issue)
- **P4** — Verified custom sending domain for Resend
- **P4** — Delete/soft-delete of uploaded files (currently `is_deleted` flag never toggled)
