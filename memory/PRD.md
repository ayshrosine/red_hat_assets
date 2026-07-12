# AssetFlow — PRD & Build Log

## Original Problem Statement
Enterprise Asset & Resource Management Web App (React + FastAPI + MongoDB). Centralized ERP-style platform to track, allocate, book, maintain, and audit physical assets and shared resources. Excludes purchasing, invoicing, accounting.

## User Choices
- Auth: **Both** JWT + Emergent Google OAuth
- File storage: Emergent object storage
- Seed data: yes
- Design: inspired by wope.com — dark editorial with neon accents
- Overdue reminders: in-app + Resend email
- PDF export: client-side (jsPDF + html2canvas)

## Architecture
- **Backend:** FastAPI single-file `server.py` + helper modules (`storage.py`, `emailer.py`, `scheduler.py`). JWT httpOnly cookies + Emergent Google OAuth session cookies. bcrypt + brute-force lockout keyed by email. RBAC middleware. MongoDB via motor. Background asyncio scheduler for overdue reminders (hourly, in-memory per-day dedupe).
- **Frontend:** React 19 + Tailwind + shadcn/ui. Cabinet Grotesk (display) + Satoshi (body). AuthProvider context, protected Layout, StatusPill, FileUploader with AuthedImage (blob URL via cookie-authed fetch). Sonner toasts. Recharts + jsPDF/html2canvas for PDF export.

## What's Implemented (2026-07-12)

### Phase 1 — Auth + RBAC + Dashboard + Org Setup — ✅
- JWT register/login/logout/refresh/forgot/reset + Emergent Google OAuth session exchange
- Brute-force lockout (5 attempts → 15 min, email-keyed)
- Departments + Categories + Employees management with role promotion (Admin only)
- Dashboard: 6 stat cards, overdue banner, activity feed, quick actions

### Phase 2 — Assets — ✅
- Register asset with **Emergent object storage** photo + doc uploads (multi-file, drag-drop, previews)
- Table with search/filters + detail page with photo gallery, docs, allocation/maintenance history

### Phase 3 — Allocation & Transfer — ✅
- Allocate with expected return · **Double-allocation guard** (409 + inline warning + auto-transfer path)
- Transfer request/approve/reject with automatic allocation swap
- Return check-in · Overdue tab + visual highlighting

### Phase 4 — Resource Booking — ✅
- 7-day timeline · **Server-side overlap validation** (booking_guard) · Cancel

### Phase 5 — Maintenance Kanban — ✅
- 5-column board with auto asset-status sync (Approve → under_maintenance, Resolve → available)

### Phase 6 — Audit Cycles — ✅
- Create cycle with dept/location scope + auditor assignments + asset snapshot
- Checklist to mark verified/missing/damaged (RBAC: admins or assigned auditors)
- Auto-generated discrepancy report
- Close cycle applies mutations (missing → lost, damaged → under_maintenance) — idempotent

### Phase 7 — Reports & Analytics — ✅
- Utilization by department (bar)
- Status distribution (pie)
- Maintenance by priority (bar)
- Allocation velocity (line, demo)
- **Booking heatmap** (day × hour with intensity coloring)
- Most-used vs idle assets
- CSV export · **Client-side PDF export** (html2canvas + jsPDF)

### Phase 8 — Notifications + Activity + Reminders — ✅
- Unified notifications feed with mark-all-read
- Activity log
- **Background overdue scheduler** (hourly): fires in-app notifications + **Resend email** to each affected user, dedup'd per day
- Manual `POST /api/overdue/check` trigger for admin/asset_manager

## Testing
- Iteration 1: 18/19 backend, all frontend passed — fixed brute-force + CORS
- Iteration 2: 100% new-feature backend (uploads/audit/overdue/OAuth guard) + frontend audit flow — flagged missing FileUploader render
- Iteration 3: focused retest — **all clean, zero issues**

## Seed Credentials
See `/app/memory/test_credentials.md`.

## Backlog / Next Actions
- **P1** — Verify Google OAuth end-to-end with real Google account on production URL (guard endpoint already tested)
- **P2** — Split `server.py` (~1250 lines) into `routers/*.py` when the codebase grows
- **P2** — Short-lived signed URLs for image auth (instead of ?auth=<jwt> query param)
- **P2** — Booking recurring/reschedule
- **P3** — SMS reminders via Twilio; PWA offline mode
