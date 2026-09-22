# ACare — Aquatic Facility Management System

**Live app:** [https://uwindsor-accs.vercel.app/login](https://uwindsor-accs.vercel.app/login)

ACare is an aquatic facility management platform for the University of Windsor,
built to track aquatic populations (census), water quality, incident reports,
research projects (AUPPs), and a 14-day mandatory quarantine pipeline for new
fish. It enforces role-based access control so staff, facility managers,
admins, and university chairs — the researchers and coordinators who run day
to day operations — each get exactly the access their role needs for
compliance and daily work.

The same web build ships three ways: a browser app (Vercel), a Dockerized
local dev stack, and an Android tablet app (Capacitor, updated over the air).

---

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Getting started locally](#getting-started-locally)
- [Environment variables](#environment-variables)
- [Deployment](#deployment)
- [Web app and Android APK](#web-app-and-android-apk)
- [Database schema](#database-schema)
- [API surface](#api-surface)
- [Testing](#testing)
- [Documentation](#documentation)
- [Notes for future developers](#notes-for-future-developers)

---

## Features

- **Role-based access control:** users sign up requesting a role (Chair,
  Admin, Manager, or Staff) and wait for an Admin/Chair to approve them. A
  `super_admin` account exists only for first-boot bootstrap (see
  [Environment variables](#environment-variables)) — it is never a self-signup
  option.
- **Facility & tank management:** create and manage Facilities, Rooms, and
  Tanks; staff can be assigned to specific tanks.
- **Project (AUPP) tracking:** research projects with metadata (species, sex,
  date of birth, source) and AUPP expiry monitoring.
- **Census & population tracking:** append-only event sourcing for arrivals,
  deaths, hatches, transfers, and manual adjustments across tanks.
- **Water quality & incidents:** daily water-quality logs, test-strip logs,
  and aquatic incident reports.
- **Quarantine monitor:** enforces a 14-day mandatory isolation period for new
  arrivals, with a request/approval flow for transfer exemptions.
- **Reports dashboard:** an executive summary plus filterable table logs
  (date range, event type, project/AUPP), with CSV and PDF export.
- **Notifications:** an in-app bell (polled) on web, plus native push via
  Firebase Cloud Messaging on the Android app.
- **Audit logging:** an immutable record of actor, action, and before/after
  state for every meaningful write, for regulatory compliance.

## Architecture

This is an npm-workspaces-style monorepo (no workspace manager configured at
the root — each app manages its own dependencies):

```
MVP-Acare/
├── apps/
│   ├── api/         FastAPI backend (Python 3.13, MongoDB via Beanie ODM)
│   ├── web/          React + Vite frontend — also the source of the Android app
│   │   └── android/  Capacitor native shell (committed), package ca.uwindsor.acare
│   └── mobile/       Expo/React Native prototype — NOT built or shipped by any
│                      workflow; no device runs it (see note below)
├── packages/
│   └── forms-core/   Shared form-schema package
├── docs/              Product, design and operations documentation
├── .github/workflows/ CI: OTA bundle publishing and signed APK releases
├── docker-compose.yml Local dev stack: MongoDB + API + web
└── render.yaml        Reference blueprint mirroring the live Render service
```

**Key architectural fact:** the Android app is not a second frontend. It is
the exact same `apps/web` React/Vite build, wrapped by
[Capacitor](https://capacitorjs.com) in a native WebView shell. Same
components, same Tailwind CSS, same axios client, same API — there is no UI
code to keep in sync between web and tablet. Only truly native concerns
(export/share, printing, push notifications, the hardware back button, session
storage) branch at runtime via `isNative()` in `apps/web/src/lib/platform.ts`.
Full detail: [`apps/web/ANDROID.md`](apps/web/ANDROID.md).

`apps/mobile` is a separate Expo prototype (offline capture with an outbox
sync) explored earlier in the project. It is not wired into any deploy or
build pipeline — it exists in the repo but is not part of the shipped system.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.13), Beanie ODM over Motor (async MongoDB driver), Pydantic v2 |
| Auth | JWT (`python-jose`), password hashing via `passlib`/`argon2` |
| Database | MongoDB (MongoDB Atlas in production) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query & Table, React Router, Recharts, axios |
| Android shell | Capacitor 8 (`apps/web/android`), `@capgo/capacitor-updater` for OTA |
| Push notifications | Firebase Cloud Messaging |
| Email | Resend (HTTPS API) or SMTP — whichever is configured |
| PDF/export | `reportlab`, `pypdf` (backend); native share sheet on Android |
| Containerization | Docker (both `apps/api` and `apps/web` have Dockerfiles; `docker-compose.yml` runs the full stack) |
| CI/CD | GitHub Actions (OTA bundle publishing, signed Android release builds) |

## Getting started locally

### Option A — Docker (recommended, runs the whole stack)

**Prerequisites:** [Git](https://git-scm.com/), [Docker](https://www.docker.com/) & Docker Compose.

**1. Clone the repository**
```bash
git clone https://github.com/fishcarefrec-coder/uwindsor-accs.git MVP-Acare
cd MVP-Acare
```

**2. Build and run**
```bash
docker compose up --build
```
This starts MongoDB, the FastAPI backend, and the Vite React frontend.

**3. Access the app**
- Web app: [http://localhost:5173](http://localhost:5173)
- API: [http://localhost:8000](http://localhost:8000)
- API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

> The first time the backend starts against an empty database, it creates a
> Super Admin account. Email defaults to `SUPERADMIN_EMAIL`
> (`superadmin@uwindsor.ca` if unset). If `SUPERADMIN_PASSWORD` is set that's
> the password; otherwise a random one is generated and printed once to the
> API log — read it there, sign in, then change it. An account that already
> exists is never modified.

### Option B — Manual setup (without Docker)

Requires MongoDB (port 27017), **Python 3.13** (matches `apps/api/Dockerfile`
— a different minor version can hide stdlib differences that only surface in
production), and Node.js 18+.

**Backend (FastAPI):**
```bash
cd apps/api
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m app.seed              # seeds the Super Admin
python -m uvicorn app.main:app --port 8000 --reload
```

**Frontend (Vite + React)**, in a new terminal:
```bash
cd apps/web
npm install
npm run dev
```

From the repo root, `npm run install:all` and `npm run dev` (or `dev:unix` on
Mac/Linux) do both at once — see `package.json`.

## Environment variables

Copy `.env.example` (root) or the per-app `apps/api/.env.example` /
`apps/web/.env.example` files and fill in values. Defaults for the API are
defined in `apps/api/app/config.py`.

| Variable | Where | Purpose |
|---|---|---|
| `MONGO_URI`, `MONGODB_DB_NAME` | API | Database connection |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_HOURS` | API | JWT signing/expiry |
| `CORS_ORIGINS` | API | Extra allowed web origins (comma-separated). `https://uwindsor-accs.vercel.app` and any `*.vercel.app` are allowed by default. |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` | API | First-boot super admin (see above) |
| `FCM_SERVICE_ACCOUNT_JSON`, `FCM_ANDROID_CHANNEL_ID` | API | Firebase push credentials/channel |
| `APP_UPDATE_TOKEN`, `APP_UPDATE_ENABLED` | API | OTA bundle publishing auth + kill switch |
| `RESEND_API_KEY` or `SMTP_HOST/PORT/USERNAME/PASSWORD` | API | Email transport (neither set = mock mode) |
| `DEFAULT_SENDER_EMAIL`, `ENABLE_EMAIL_NOTIFICATIONS` | API | Sender address / master switch |
| `VITE_API_URL` | Web | The API's base URL, baked in at build time |

Full variable-by-variable reference, including what each one affects in
production: [`docs/OPERATIONS.md`](docs/OPERATIONS.md#4-environment-variables-api--set-in-render).

## Deployment

| Piece | Technology | Hosted on |
|---|---|---|
| API | FastAPI, Docker | **Render** — web service `uwindsor-accs` (Oregon, Standard plan) |
| Web app | React + Vite | **Vercel** — project `uwindsor-accs` |
| Database | MongoDB | **MongoDB Atlas** |
| Android app | Capacitor-wrapped web build | Sideloaded APK via **GitHub Releases**; frontend updates ship **over the air (OTA)** |
| Push notifications | Firebase Cloud Messaging | Firebase project `acare-uwindsor` |
| CI/CD | — | **GitHub Actions** (`.github/workflows`) |

**Render (API):** Docker runtime, root directory `apps/api`, auto-deploys on
every commit to `main`. The container's start command runs
`python -m app.seed` (idempotent super-admin bootstrap) and then uvicorn.
`render.yaml` in the repo root is a *reference* blueprint documenting these
settings — the live service was created directly in the Render dashboard, not
from this file. The service URL must stay stable: it's baked into every
installed Android APK.

**Vercel (web):** framework preset Vite, root directory `apps/web`, build
command `npm run build`, output directory `dist`, production branch `main`.
`apps/web/vercel.json` rewrites all routes to `index.html` for client-side
routing.

**MongoDB Atlas:** the database backing the API in production, referenced via
`MONGO_URI`/`MONGODB_DB_NAME` in Render's environment.

**GitHub Actions / OTA for the Android app:** the Android app does **not**
load its UI from Vercel — its assets are bundled into the APK and served
locally, with only API calls going over the network. When `apps/web/src`
changes and merges to `main`, `.github/workflows/ota-bundle.yml`:
1. builds `apps/web` against `.env.mobile`,
2. zips `dist/` and uploads it as a GitHub Release asset, then
3. registers that bundle with the API (`POST /app-updates/bundles`), guarded
   by a shared `APP_UPDATE_TOKEN`.

Installed tablets check `POST /app-updates/check` on launch, download and
verify the bundle by SHA-256, and apply it on the next cold start — no
reinstall, no cable. A separate workflow,
`.github/workflows/release-apk.yml`, only runs when something under
`apps/web/android/` or `capacitor.config.ts` changes (i.e. the *native* shell,
not the JS/UI), and produces a signed APK attached to a GitHub Release.

> **Never push directly to `main`** — it deploys to production (Vercel +
> Render) and, for the `dev` branch too, also publishes an OTA bundle to
> tablets. Treat both branches as release branches. See
> [`docs/OPERATIONS.md`](docs/OPERATIONS.md) section 8.

## Web app and Android APK

- **Web app:** standard React SPA served by Vercel at
  [uwindsor-accs.vercel.app](https://uwindsor-accs.vercel.app/login). Talks to
  the Render API over `VITE_API_URL`.
- **Android app (tablets):** the identical web UI, compiled once and wrapped
  in a Capacitor native shell (`apps/web/android`, package
  `ca.uwindsor.acare`). Distributed as a sideloaded APK via GitHub Releases —
  **not** the Play Store. Frontend-only changes reach installed tablets
  automatically over the air on next launch; native changes (a new Capacitor
  plugin, a permission, a Gradle bump) require a new signed APK installed
  manually over the old one.
- Four behaviors differ between web and Android at runtime (export/share,
  printing, session storage, and notifications) — all are documented with
  rationale in [`apps/web/ANDROID.md`](apps/web/ANDROID.md#what-differs-from-the-web-build).
- The Android release signing keystore is **not** in the repository and is
  **not recoverable from it**. If it's ever lost, no future APK can update an
  already-installed app in place — every tablet would need to uninstall and
  reinstall. Keep encrypted backups outside the repo (see
  [`docs/OPERATIONS.md`](docs/OPERATIONS.md#6-android-tablets)).

## Database schema

MongoDB via the Beanie ODM. Data favors **immutability** for compliance:
census events, water-quality logs, incident reports, and audit logs are
append-only — corrections are new entries, not edits.

| Collection | Purpose | Key fields |
|---|---|---|
| `users` | Accounts and permissions | `email`, `password_hash`, `first_name`, `last_name`, `role` (`super_admin`/`chair`/`admin`/`manager`/`staff`), `status` (pending/approved/rejected), `assigned_tank_ids`, `facility_ids`, `room_ids` |
| `projects` | Research projects (AUPPs) | `title`, `pi_name`, `aupp_number` (unique), `status`, `species`, `sex`, `dob`, `established_date`, `source`, `aupp_expiry_date` |
| `facilities`, `rooms`, `tanks` | Hierarchical location structure | Tanks carry `status` and quarantine metadata (`is_quarantined`, `quarantine_start_date`, `quarantine_end_date`) |
| `tank_assignments` | Links a project to a tank | `project_id`, `tank_id`, `current_count`, `aupp_number` — real-time active population for that tank |
| `water_quality_logs` | Daily/test-strip water readings (append-only) | `type`, `date`, `parameters`, `project_id` |
| `incident_reports` | Aquatic incidents (append-only) | `problem`, `treatment`, `aquatic_condition_checked`, `vet_contacted` |
| `census_events` | Population change log (append-only) | `change` (signed int delta), `date`, `project_id`, `tank_id`, `event type` (arrival/death/transfer_in/transfer_out/hatch/manual_adjustment) — sums to `tank_assignment.current_count` |
| `audit_logs` | Compliance trail (append-only) | `actor`, `action`, `entity_type`, `before`, `after` |
| `individual_fish` | Per-animal tracking | see `apps/api/app/models/individual_fish.py` |
| `device_tokens` | Registered push tokens | one per signed-in device; `disabled_at`/`last_error` on FCM rejection |
| `app_bundles` | OTA bundle registry | version pointers, `min_version_code`, active/inactive state |
| `notifications`, `notification_settings`, `notification_sweep_state` | In-app/push alerts, per-user preferences, and sweep bookkeeping | — |
| `email_logs` | Outbound email records | — |
| `species` | Species reference data | — |

Full model definitions live under `apps/api/app/models/`; a narrative version
is in [`docs/backend-schema.md`](docs/backend-schema.md).

## API surface

FastAPI app (`apps/api/app/main.py`), interactive docs at `/docs` on any
running instance. Routers, one per domain area, under `apps/api/app/routers/`:

`auth`, `users`, `facilities`, `water_quality_logs`, `incident_reports`,
`projects`, `census`, `transfers`, `intake`, `species`, `dashboard`,
`reports`, `audit`, `quarantine`, `individual_fish`, `export`, `sync`,
`notifications`, `app_updates`.

Full endpoint-by-endpoint reference: [`docs/API-documentation.md`](docs/API-documentation.md).

## Testing

Backend acceptance tests cover full end-to-end flows (signup, approval,
assignments, quarantine, notifications, exports, sync, and more) and live in
`apps/api/tests/`:

```bash
cd apps/api
# with your virtual environment active and MongoDB running locally
python -m pytest -s -v
```

## Documentation

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — **start here to take over the
  project.** Deploys, environment variables, accounts, Android release
  process, secret rotation.
- [`apps/web/ANDROID.md`](apps/web/ANDROID.md) — Android build, OTA updates,
  and push notifications in depth.
- [`docs/PRD.md`](docs/PRD.md), [`docs/TRD.md`](docs/TRD.md) — product and
  technical requirements.
- [`docs/API-documentation.md`](docs/API-documentation.md) — API reference.
- [`docs/backend-schema.md`](docs/backend-schema.md) — database schema in
  detail.
- [`docs/UIUX-design.md`](docs/UIUX-design.md) — design decisions.
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — build
  history/roadmap.

## Notes for future developers

- **`dev` is not a private staging branch.** A push to `dev` also publishes an
  OTA bundle to tablets, and `dev` work has previously reached the live
  database. Treat pushes to both `dev` and `main` as releases.
- **The repository must stay public.** Tablets download OTA bundles from
  GitHub Release assets unauthenticated; going private breaks that channel
  unless storage is moved to an authenticated source.
- **Startup migrations run against the live database on every API deploy.**
  Check data impact before pushing schema or index changes.
- **The Android package name `ca.uwindsor.acare` must never change** — it's
  the app's identity for updates and Firebase.
- **The Render service must stay on a paid plan** (or an equivalent
  always-on host). A free/sleeping tier would miss the periodic notification
  sweep; it self-heals on the next pass if that ever happens, but alerts would
  be late.
- Scanned university source documents (PDFs referenced in `docs/`) are
  intentionally excluded from the repository, since it's public.
- For anything not covered here, [`docs/OPERATIONS.md`](docs/OPERATIONS.md) is
  the authoritative operations reference and includes a first-day checklist
  for a new owner.
