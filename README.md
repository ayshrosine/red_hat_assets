# Here are your Instructions
Building AssetFlow — Enterprise Asset & Resource Management SaaS
Build prompt for an AI coding agent — Bun + Next.js + Prisma (SQL) + Vercel
You have an empty turborepo that we want to set up for a new project I'm building. This project digitizes how organizations track, allocate, and maintain physical assets and shared resources (equipment, furniture, vehicles, rooms) through a centralized ERP-style platform — think an internal “asset & resource ops” SaaS usable by any organization (offices, schools, hospitals, factories, agencies). It covers organization setup, asset lifecycle tracking, allocation/transfer with conflict handling, resource booking with overlap validation, a maintenance approval workflow, structured audit cycles, analytics, and notifications. It does NOT touch purchasing, invoicing, or accounting.
Step 1 — Project Setup & Architecture
For now we want to set up all the services needed for this project. The architecture looks as follows:
Monorepo
•Use the existing empty Turborepo. Use Bun as the package manager and script runner for the whole repo (bun install, bunx, bun run).
•Structure: apps/web for the frontend+backend, packages/db for the Prisma layer, packages/ui for shared React components (optional, scaffold empty), packages/config for shared ESLint/TS config.
Frontend + Backend — apps/web
•A single Next.js app (App Router, TypeScript) initialised with Bun (bun create next-app or equivalent), styled with Tailwind CSS.
•This app serves both the UI and the API: use Next.js Route Handlers (app/api/**/route.ts) as our CRUD/backend layer instead of a separate Express service, since we're deploying serverlessly on Vercel.
•Use server actions where it simplifies form handling (e.g. Organization Setup CRUD), and route handlers for anything the client fetches dynamically (dashboard KPIs, search/filter, notifications polling).
Database Layer — packages/db
•PostgreSQL as the SQL database (assume Vercel Postgres or Neon for hosting; connection string comes from env).
•Prisma ORM lives entirely in packages/db: schema.prisma, migrations, a generated client, and a typed seed script.
•Export a singleton PrismaClient from packages/db (e.g. packages/db/src/client.ts) and consume it from apps/web via a workspace dependency — do not duplicate schema or client instantiation in the web app.
•Model the core entities now (fields can be refined later): Organization, Department (with parentDepartment for hierarchy), AssetCategory, Employee/User (linked to auth identity, department, role), Asset (with lifecycle status enum: Available, Allocated, Reserved, Under Maintenance, Lost, Retired, Disposed), Allocation, TransferRequest, Resource/Booking, MaintenanceRequest, AuditCycle + AuditItem, Notification, ActivityLog.
•Role enum on Employee: Admin, Asset Manager, Department Head, Employee — roles are only ever assigned by an Admin (see Step 2), never self-selected at signup.
File / Object Storage
•Since we're deploying on Vercel (no Docker/self-hosted object store), use Vercel Blob for storing asset photos, supporting documents, maintenance request photos, and audit attachments.
•Wrap upload/download/delete behind a small storage helper (e.g. packages/db or a new packages/storage) so the provider can be swapped later without touching feature code.
Authentication
•Use NextAuth.js (Auth.js) configured for two providers: Google OAuth and Email/Password (credentials).
•Signup only ever creates a plain Employee account — no role selection is exposed on the signup form. Role elevation to Department Head / Asset Manager happens exclusively from the Admin's Employee Directory (Screen 3, Tab C).
•Session must carry the user's role and department so route handlers and pages can enforce role-based access.
No Docker / No docker-compose
•We are deploying to Vercel, not containers — skip Dockerfiles and docker-compose entirely. Local development runs directly via Bun against a Postgres instance (local Postgres, Neon dev branch, or Vercel Postgres) and Vercel Blob (or its local dev emulation).
Docs & Environment
•Write clear steps to run the project locally in the README (install deps with Bun, set up .env, run Prisma migrate + seed, start the dev server).
•Mirror the same setup steps in AGENTS.md so any AI coding agent working in this repo knows how to bootstrap and run it.
•Add a .env.example to the repo root and to apps/web / packages/db as needed, covering: DATABASE_URL, NEXTAUTH_URL, NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, BLOB_READ_WRITE_TOKEN. I will supply real values later — just stub them for now.
•Add top-level package.json scripts to install, generate the Prisma client, run migrations, seed, and start the app locally with a single command (e.g. bun run dev, bun run db:migrate, bun run db:seed).
Step 2 — Data Model, Roles & Workflow Rules
Before wiring up screens, make sure the Prisma schema and shared types encode these rules, since almost every screen depends on them:
Roles (assigned only via Screen 3, Tab C — never at signup)
•Admin — manages departments, asset categories, audit cycles, and role assignment; views organization-wide analytics.
•Asset Manager — registers/allocates assets; approves transfers, maintenance requests, audit discrepancy resolution and returns.
•Department Head — views assets allocated to their department; approves allocation/transfer requests within it; books resources on the department's behalf.
•Employee — views assets allocated to them; books resources; raises maintenance requests; initiates return/transfer requests.
Asset lifecycle
•States: Available, Allocated, Reserved, Under Maintenance, Lost, Retired, Disposed.
•Transitions are triggered by workflows, not free edits: Available → Allocated (allocation), Allocated → Available (return), Available ↔ Under Maintenance (maintenance approval/resolution), Available/Allocated → Lost (confirmed-missing at audit close), any → Retired/Disposed (explicit admin/manager action).
Conflict rules to enforce server-side
•Double-allocation block: an asset already allocated cannot be allocated again — the API must reject it, report who currently holds it, and the UI offers a Transfer Request instead.
•Booking overlap validation: two bookings for the same resource cannot overlap in time; a back-to-back booking (starts exactly when the previous ends) is allowed.
•Overdue detection: allocations past their Expected Return Date, and bookings/maintenance past expected timelines, must be computable via a query (cron/edge function or on-read calculation) that feeds the Dashboard and Notifications.
Step 3 — Screens & Features
Build these ten screens end-to-end (UI + route handlers/server actions + Prisma queries), matching the attached mockups. Each screen lists its purpose and required functionality.
1. Login / Signup
•Email/password and Google sign-in via NextAuth; “Forgot password” flow; session validation on protected routes.
•Signup creates an Employee account only — copy on the form should make clear roles are assigned later by an Admin, matching the mockup's “Sign up creates an employee account, admin roles assigned later” note.
2. Dashboard / Home
•KPI cards: Assets Available, Assets Allocated, Maintenance Today, Active Bookings, Pending Transfers, Upcoming Returns.
•Overdue returns shown in a visually distinct (e.g. red) banner, separate from the upcoming-returns KPI.
•Quick actions: Register Asset, Book Resource, Raise Maintenance Request — plus a Recent Activity feed.
3. Organization Setup (Admin only — 3 tabs)
◦Tab A — Departments: create/edit/deactivate; assign Department Head, optional parent department, Active/Inactive status.
◦Tab B — Asset Categories: create/edit categories (Electronics, Furniture, Vehicles, ...) with optional category-specific fields (e.g. warranty period).
◦Tab C — Employee Directory: list Name/Email/Department/Role/Status; this is the only screen where an Admin promotes an Employee to Department Head or Asset Manager.
•Editing a department here must drive the picklists used on the Asset Registration and Directory screens.
4. Asset Registration & Directory
•Register: Name, Category (from Screen 3), auto-generated Asset Tag (e.g. AF-0001), Serial Number, Acquisition Date, Acquisition Cost (kept for ranking/reports only — not linked to accounting), Condition, Location, photo/documents upload (to Vercel Blob), and a shared/bookable flag.
•Directory table with search/filter by Asset Tag, Serial Number, QR code, category, status, department, or location; shows current lifecycle status per row.
•Per-asset detail view with allocation history and maintenance history.
5. Asset Allocation & Transfer
•Allocate an asset to an employee/department with an optional Expected Return Date.
•Enforce the double-allocation block described in Step 2, with the “currently held by …” message and a Transfer Request button, matching the mockup's red warning state.
•Transfer workflow: Requested → Approved (by Asset Manager/Department Head) → Re-allocated, with allocation history updated automatically.
•Return flow: mark returned, capture condition check-in notes, revert asset status to Available.
•Overdue allocations auto-flag and feed the Dashboard and Notifications.
6. Resource Booking
•Calendar/timeline view of a resource's existing bookings for a given day.
•Enforce the overlap validation described in Step 2, matching the mockup's conflict message (“requested 9:30–10:30 conflicts — slot is unusable”).
•Booking status: Upcoming, Ongoing, Completed, Cancelled; support cancel/reschedule and a reminder notification before the slot starts.
7. Maintenance Management
•Raise request: select asset, describe issue, set priority, attach a photo (Vercel Blob upload).
•Kanban-style workflow board: Pending → Approved/Rejected (by Asset Manager) → Technician Assigned → In Progress → Resolved.
•Asset status auto-updates to Under Maintenance on approval and back to Available on resolution; maintenance history retained per asset.
8. Asset Audit
•Create an audit cycle scoped by department/location and date range; assign one or more auditors.
•Auditor marks each in-scope asset Verified / Missing / Damaged; system auto-generates a discrepancy report for flagged items.
•Close Audit Cycle locks the cycle and updates affected asset statuses (e.g. confirmed-missing → Lost); audit history retained per cycle.
9. Reports & Analytics
•Asset utilization by department, most-used vs. idle assets, maintenance frequency by asset/category, assets due for maintenance or nearing retirement, department-wise allocation summary, and a resource booking heatmap.
•Support an “Export report” action (CSV/PDF).
10. Activity Logs & Notifications
•Notification types: Asset Assigned, Maintenance Approved/Rejected, Booking Confirmed/Cancelled/Reminder, Transfer Approved, Overdue Return Alert, Audit Discrepancy Flagged.
•Filterable feed (All / Alerts / Approvals / Bookings) plus a full activity log of admin/manager/employee actions (who did what, when), for auditability.
Step 4 — Cross-Cutting Requirements
•Role-based access control on every route handler/server action, not just hidden UI — e.g. only Admins can hit the promote-to-role endpoint, only Asset Managers/Department Heads can approve transfers.
•Responsive layout with a persistent left sidebar (Dashboard, Organization Setup, Assets, Allocation & Transfer, Resource Booking, Maintenance, Audit, Reports, Notifications) matching the attached mockups.
•Keep the module boundaries clean and reusable (e.g. a shared “conflict-checked allocate” function, a shared “overlap-checked book” function) so future modules can reuse the same validation logic.
•Do not build purchasing, invoicing, or accounting features — Acquisition Cost is stored for reporting only.
•By the end, add a script/command to install dependencies, run Prisma migrate + seed, and start the Next.js app locally with a single command, and document the same in README.md and AGENTS.md.
Reference
•Mockups: 10 screens covering Login/Signup, Dashboard, Organization Setup, Asset Registration & Directory, Allocation & Transfer, Resource Booking, Maintenance Management, Asset Audit, Reports & Analytics, and Activity Logs & Notifications (attached).
•Problem statement: AssetFlow — Enterprise Asset & Resource Management System (attached).