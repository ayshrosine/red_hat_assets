# AssetFlow — PRD & Build Log

## Original Problem Statement
Enterprise Asset & Resource Management Web App (React + FastAPI + MongoDB). Centralized ERP-style platform for organizations to digitize how they track, allocate, book, maintain, and audit physical assets and shared resources. Explicitly excludes purchasing, invoicing, and accounting. 10 screens spanning Auth → Dashboard → Org Setup → Assets → Allocation & Transfer → Booking → Maintenance → Audit → Reports → Notifications.

## User Choices (2026-07-12)
- Auth: **Both** JWT (email+password) and Emergent Google OAuth
- File storage: Emergent object storage (deferred to Phase 2 iteration)
- Seed data: **yes** (admin + sample departments/categories/assets)
- Scope for first finish: **Phases 1–5 deep**; Phases 6–8 stubbed
- Design inspiration: wope.com — dark, editorial, neon-accent

## User Personas
- **Admin** — Manages departments, categories, audit cycles, promotes users.
- **Asset Manager** — Registers assets, allocates, approves transfers.
- **Department Head** — Views/approves within dept.
- **Employee** — Views own assets, books resources, raises maintenance.

## Architecture
- **Backend:** FastAPI single-file `server.py`, JWT (httpOnly cookies) + Emergent Google OAuth session cookies, bcrypt password hashing, brute-force lockout keyed by email, RBAC middleware via `require_roles`, MongoDB with async motor, seed on startup.
- **Frontend:** React 19 + Tailwind + shadcn/ui, dark theme with Cabinet Grotesk (display) and Satoshi (body) fonts from Fontshare CDN, `AuthProvider` context, `Layout` (sidebar + topbar), status pills, per-route protection with role gating. Sonner for toasts. Recharts for analytics.

## What's Implemented (2026-07-12)
### Phase 1 — Auth, RBAC, Layout, Dashboard, Org Setup — ✅
- JWT register/login/logout/refresh/forgot-password/reset-password endpoints
- Emergent Google OAuth (`/auth/google/session`) exchange endpoint with race-safe callback handling
- Brute-force lockout (5 attempts → 15 min, keyed by email — proxy safe)
- Admin/manager/head/employee seed users
- Departments + Categories + Employees management with role promotion (Admin only)
- Dashboard: 6 stat cards, overdue banner, activity feed, quick actions, status distribution bar

### Phase 2 — Assets Registration & Directory — ✅
- Register asset dialog (name, tag, serial, category, dept, location, condition, bookable flag, photo URL, cost, notes, custom_data)
- Table with search + filters (category, status, dept, bookable)
- Detail page with allocation + maintenance history + quick actions

### Phase 3 — Allocation & Transfer — ✅
- Allocate with expected return
- **Double-allocation guard** (409 with current holder info + inline warning banner + auto-open transfer dialog)
- Transfer flow (request → approve/reject) — approver auto-closes prior allocation & opens new one
- Return check-in with condition notes
- Overdue detection (visual highlight + separate tab)

### Phase 4 — Resource Booking — ✅
- 7-day timeline view per resource
- Datetime-local booking form
- **Server-side overlap validation** (booking_guard) — 409 with conflict details
- Cancel booking

### Phase 5 — Maintenance Kanban — ✅
- 5-column board: Pending → Approved → Assigned → In Progress → Resolved (+ Rejected side tray)
- Approve auto-sets asset to `under_maintenance`; Resolve auto-sets to `available`
- Priority pills, per-card action buttons, RBAC-gated

### Phases 6–8 (lite/stubbed)
- **Audit** — placeholder page
- **Reports** — utilization bar chart, status distribution pie, maintenance priority, allocation velocity line, CSV export of assets
- **Notifications** — unified feed with 2 tabs (Notifications + Activity log), mark-all-read

## Testing
- Backend: 18/19 pytest passes, fixed brute-force lockout after iteration 1
- Frontend: all E2E flows passed (login → dashboard → assets → maintenance → logout)

## Seed Credentials (see `/app/memory/test_credentials.md`)
- admin@assetflow.io / admin123 (admin)
- manager@assetflow.io / manager123 (asset_manager)
- head@assetflow.io / head123 (department_head)
- employee@assetflow.io / employee123 (employee)

## Backlog / Next Actions (P0 → P2)
- **P0** — Object storage integration for asset photo/doc uploads (drag-drop + preview)
- **P0** — Audit cycles: create, checklist verification, discrepancy report, close-cycle status mutations
- **P1** — Reports: booking heatmap, PDF export, most-used vs idle report
- **P1** — Overdue reminder scheduler (cron/queue) — currently only visual detection
- **P1** — Google OAuth: verify end-to-end with real credential on production redirect
- **P2** — Split `server.py` into `routers/*.py` for maintainability
- **P2** — Booking recurring/rescheduling, email notifications
- **P2** — Mobile-first responsive polish (currently desktop-first)
