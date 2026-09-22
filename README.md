# ACare: Aquatic Facility Management System

**Live app:** [https://uwindsor-accs.vercel.app/login](https://uwindsor-accs.vercel.app/login)

ACare is an aquatic facility management platform built for the University of Windsor. It tracks aquatic populations (census), water quality, incident reports, research projects (AUPPs), and a 14-day mandatory quarantine pipeline for new fish. Role-based access control ensures staff, facility managers, admins, and university chairs receive appropriate permissions for daily operations and regulatory compliance.

The web build runs in three environments: a browser app (Vercel), a Dockerized local development stack, and an Android tablet app (Capacitor with over-the-air updates).

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

- **Role-based access control:** Users sign up requesting a role (Chair, Admin, Manager, or Staff) pending Admin/Chair approval. A `super_admin` account exists only for initial bootstrap (see [Environment variables](#environment-variables)) and cannot be selected during self-signup.
- **Facility & tank management:** Create and manage Facilities, Rooms, and Tanks, with staff assigned to specific tanks.
- **Project (AUPP) tracking:** Manage research projects with metadata (species, sex, date of birth, source) and monitor AUPP expiration dates.
- **Census & population tracking:** Append-only event sourcing for arrivals, deaths, hatches, transfers, and manual population adjustments across tanks.
- **Water quality & incidents:** Record daily water-quality logs, test-strip readings, and aquatic incident reports.
- **Quarantine monitor:** Enforce a mandatory 14-day isolation period for new arrivals, with a request/approval flow for transfer exemptions.
- **Reports dashboard:** Access executive summaries and filterable event logs (by date range, event type, or project/AUPP) with CSV and PDF export options.
- **Notifications:** In-app notifications for web users and native push notifications via Firebase Cloud Messaging for Android tablets.
- **Audit logging:** Maintain immutable records of users, actions, and state changes for regulatory compliance.

## Architecture

This project is organized as an npm-workspaces monorepo where each app manages its dependencies:

```
MVP-Acare/
├── apps/
│   ├── api/         FastAPI backend (Python 3.13, MongoDB via Beanie ODM)
│   ├── web/          React + Vite frontend (also builds the Android app)
│   │   └── android/  Capacitor native shell, package ca.uwindsor.acare
│   └── mobile/       Expo/React Native prototype (inactive archive)
├── packages/
│   └── forms-core/   Shared form-schema package
├── docs/              Product, design, and operations documentation
├── .github/workflows/ CI: OTA bundle publishing and signed APK releases
├── docker-compose.yml Local dev stack: MongoDB + API + web
└── render.yaml        Reference blueprint mirroring the live Render service
```

The Android app uses the same `apps/web` React and Vite codebase wrapped in a native WebView shell using [Capacitor](https://capacitorjs.com). Both platforms share UI components, styling, API integration, and business logic. Platform-specific features (such as file sharing, printing, native push notifications, hardware back button handling, and session storage) branch at runtime via `isNative()` in `apps/web/src/lib/platform.ts`. For complete details, see [`apps/web/ANDROID.md`](apps/web/ANDROID.md).

`apps/mobile` contains an earlier Expo prototype developed for offline data capture. It is not part of the active build or deployment pipeline.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.13), Beanie ODM over Motor (async MongoDB driver), Pydantic v2 |
| Auth | JWT (`python-jose`), password hashing via `passlib`/`argon2` |
| Database | MongoDB (MongoDB Atlas in production) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query & Table, React Router, Recharts, axios |
| Android shell | Capacitor 8 (`apps/web/android`), `@capgo/capacitor-updater` for OTA |
| Push notifications | Firebase Cloud Messaging |
| Email | Resend (HTTPS API) or SMTP (based on configuration) |
| PDF/export | `reportlab`, `pypdf` (backend); native share sheet on Android |
| Containerization | Docker (Dockerfile per app; `docker-compose.yml` for local stack) |
| CI/CD | GitHub Actions (OTA bundle publishing, signed Android release builds) |

## Getting started locally

### Option A: Docker (recommended)

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

> When starting against an empty database, the backend creates an initial Super Admin account. The email defaults to `SUPERADMIN_EMAIL` (`superadmin@uwindsor.ca` if unset). If `SUPERADMIN_PASSWORD` is set, that password is used; otherwise, a random password is generated and logged by the API on startup. Existing accounts are not overwritten.

### Option B: Manual setup

Requires MongoDB (port 27017), **Python 3.13** (matching `apps/api/Dockerfile` to ensure standard library compatibility), and Node.js 18+.

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

From the repository root, running `npm run install:all` and `npm run dev` (or `dev:unix` on Mac/Linux) starts both services concurrently (see `package.json`).

## Environment variables

Copy `.env.example` at the repository root or the configuration files in `apps/api/.env.example` and `apps/web/.env.example`. Default configurations for the backend are defined in `apps/api/app/config.py`.

| Variable | Where | Purpose |
|---|---|---|
| `MONGO_URI`, `MONGODB_DB_NAME` | API | Database connection |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_HOURS` | API | JWT signing and expiration |
| `CORS_ORIGINS` | API | Allowed origins (comma-separated). `https://uwindsor-accs.vercel.app` and `*.vercel.app` domains are enabled by default. |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` | API | Initial super admin credentials |
| `FCM_SERVICE_ACCOUNT_JSON`, `FCM_ANDROID_CHANNEL_ID` | API | Firebase push notification configuration |
| `APP_UPDATE_TOKEN`, `APP_UPDATE_ENABLED` | API | OTA bundle publishing authentication and feature switch |
| `RESEND_API_KEY` or `SMTP_HOST/PORT/USERNAME/PASSWORD` | API | Email transport settings (defaults to mock mode if unconfigured) |
| `DEFAULT_SENDER_EMAIL`, `ENABLE_EMAIL_NOTIFICATIONS` | API | Sender address and global email switch |
| `VITE_API_URL` | Web | API base URL compiled into the frontend build |

For detailed descriptions of all environment variables, see [`docs/OPERATIONS.md`](docs/OPERATIONS.md#4-environment-variables-api--set-in-render).

## Deployment

| Component | Technology | Hosting |
|---|---|---|
| API | FastAPI, Docker | **Render** (web service `uwindsor-accs`) |
| Web app | React + Vite | **Vercel** (project `uwindsor-accs`) |
| Database | MongoDB | **MongoDB Atlas** |
| Android app | Capacitor WebView | Sideloaded APK via **GitHub Releases** with **Over-The-Air (OTA)** frontend updates |
| Push notifications | Firebase Cloud Messaging | Firebase project `acare-uwindsor` |
| CI/CD | GitHub Actions | Workflows in `.github/workflows` |

**Render (API):** Uses Docker runtime with root directory `apps/api`, automatically deploying on commits to `main`. The container start command runs `python -m app.seed` followed by `uvicorn`. The `render.yaml` file in the repository root serves as a reference configuration.

**Vercel (web):** Configured for Vite with root directory `apps/web`, build command `npm run build`, and output directory `dist` on the `main` branch. `apps/web/vercel.json` handles URL rewrites for single-page routing.

**MongoDB Atlas:** Provides the hosted database for the API production environment.

**GitHub Actions / OTA Updates:** The Android application bundles static assets directly inside the APK rather than loading from Vercel. Network requests communicate directly with the API. When changes in `apps/web/src` merge to `main`, `.github/workflows/ota-bundle.yml`:
1. Builds `apps/web` using `.env.mobile`.
2. Archives `dist/` and uploads the file to GitHub Releases.
3. Registers the update bundle with the API endpoint `POST /app-updates/bundles` using `APP_UPDATE_TOKEN`.

Installed devices check `POST /app-updates/check` on startup, verify the bundle SHA-256 checksum, and apply updates on the next application launch. Native changes to `apps/web/android/` or `capacitor.config.ts` trigger `.github/workflows/release-apk.yml` to generate a signed APK.

> **Important:** Pushing to `main` or `dev` triggers automated production builds and OTA updates. Treat both branches as active release branches. See [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

## Web app and Android APK

- **Web app:** Single-page React application hosted on Vercel at [uwindsor-accs.vercel.app](https://uwindsor-accs.vercel.app/login), communicating with the Render API via `VITE_API_URL`.
- **Android app (tablets):** Shares the same web frontend packaged into a Capacitor shell (`apps/web/android`, package `ca.uwindsor.acare`). Distributed as a sideloaded APK via GitHub Releases. Web updates deliver automatically over the air, while native configuration changes require a manual APK installation.
- Runtime differences between web and native environments (such as file exporting, printing, storage, and notifications) are documented in [`apps/web/ANDROID.md`](apps/web/ANDROID.md#what-differs-from-the-web-build).
- The release signing keystore is stored securely outside the repository. Back up keystore files separately to ensure future APK compatibility (see [`docs/OPERATIONS.md`](docs/OPERATIONS.md#6-android-tablets)).

## Database schema

MongoDB managed via Beanie ODM. The schema emphasizes immutability for compliance: census records, water-quality logs, incident reports, and audit logs are append-only.

| Collection | Purpose | Key fields |
|---|---|---|
| `users` | Accounts and permissions | `email`, `password_hash`, `first_name`, `last_name`, `role` (`super_admin`/`chair`/`admin`/`manager`/`staff`), `status` (pending/approved/rejected), `assigned_tank_ids`, `facility_ids`, `room_ids` |
| `projects` | Research projects (AUPPs) | `title`, `pi_name`, `aupp_number` (unique), `status`, `species`, `sex`, `dob`, `established_date`, `source`, `aupp_expiry_date` |
| `facilities`, `rooms`, `tanks` | Facility hierarchy | Tanks track `status` and quarantine state (`is_quarantined`, `quarantine_start_date`, `quarantine_end_date`) |
| `tank_assignments` | Project to tank mapping | `project_id`, `tank_id`, `current_count`, `aupp_number` (active population count) |
| `water_quality_logs` | Water quality measurements | `type`, `date`, `parameters`, `project_id` (append-only) |
| `incident_reports` | Aquatic incident records | `problem`, `treatment`, `aquatic_condition_checked`, `vet_contacted` (append-only) |
| `census_events` | Population change log | `change` (delta), `date`, `project_id`, `tank_id`, `event type` (arrival, death, transfer, hatch, adjustment) (sums to `tank_assignment.current_count`) |
| `audit_logs` | Audit trail | `actor`, `action`, `entity_type`, `before`, `after` (append-only) |
| `individual_fish` | Per-animal tracking | Defined in `apps/api/app/models/individual_fish.py` |
| `device_tokens` | Registered push tokens | Device token mappings with error handling for FCM |
| `app_bundles` | OTA bundle registry | Version trackers and bundle status |
| `notifications`, `notification_settings`, `notification_sweep_state` | Alerts and user preferences | In-app notification state and delivery preferences |
| `email_logs` | Outbound email records | Sent email log records |
| `species` | Species reference data | Reference taxonomy data |

Complete model definitions are located in `apps/api/app/models/`. Additional database documentation is available in [`docs/backend-schema.md`](docs/backend-schema.md).

## API surface

The FastAPI backend (`apps/api/app/main.py`) provides interactive Swagger documentation at `/docs`. Domain routes are organized in `apps/api/app/routers/`:

`auth`, `users`, `facilities`, `water_quality_logs`, `incident_reports`, `projects`, `census`, `transfers`, `intake`, `species`, `dashboard`, `reports`, `audit`, `quarantine`, `individual_fish`, `export`, `sync`, `notifications`, `app_updates`.

See [`docs/API-documentation.md`](docs/API-documentation.md) for endpoint details.

## Testing

Backend test suites cover signup, approval, assignment, quarantine, notifications, export, and sync workflows in `apps/api/tests/`:

```bash
cd apps/api
python -m pytest -s -v
```

## Documentation

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md): Operations guide covering deployments, environment setup, account setup, Android releases, and key management.
- [`apps/web/ANDROID.md`](apps/web/ANDROID.md): Android build instructions, OTA update mechanics, and push notification configuration.
- [`docs/PRD.md`](docs/PRD.md) & [`docs/TRD.md`](docs/TRD.md): Product and technical specification documents.
- [`docs/API-documentation.md`](docs/API-documentation.md): Comprehensive API reference.
- [`docs/backend-schema.md`](docs/backend-schema.md): Detailed database schema guide.
- [`docs/UIUX-design.md`](docs/UIUX-design.md): User interface design guidelines.
- [`docs/implementation-plan.md`](docs/implementation-plan.md): Project implementation timeline.

## Notes for future developers

- Pushes to `dev` and `main` trigger automated build and OTA publication tasks. Treat both branches as production release channels.
- Keep the repository public to support unauthenticated OTA bundle downloads for mobile devices.
- Database migrations execute automatically during deployment. Verify schema changes before pushing updates.
- Maintain the Android package identifier (`ca.uwindsor.acare`) to preserve compatibility with existing app installs and Firebase services.
- Host the backend on a continuous service instance to maintain background notification sweeps.
- Refer to [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for full operational documentation.
