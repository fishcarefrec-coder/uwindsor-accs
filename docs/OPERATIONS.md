# ACARE — Operations & Handover Runbook

This is the single page a new owner needs to run, deploy and maintain ACARE.
It contains **no secrets**. Values live in the hosting dashboards and in the
owner's password manager; this page only says where they are and what they do.

Related: [`README.md`](../README.md) (local setup), [`apps/web/ANDROID.md`](../apps/web/ANDROID.md)
(Android build, OTA and push in depth), and the design docs in this folder
(`PRD.md`, `TRD.md`, `API-documentation.md`, `backend-schema.md`, `UIUX-design.md`,
`implementation-plan.md`).

---

## 1. What the system is

| Piece | Tech | Hosted on |
|---|---|---|
| API | FastAPI (Python 3.13), Beanie/MongoDB, Docker | Render web service `uwindsor-accs` (Oregon, Standard plan) |
| Web app | React + Vite (`apps/web`) | Vercel project `uwindsor-accs` |
| Database | MongoDB | MongoDB Atlas |
| Tablet app | The same web build wrapped by Capacitor, package `ca.uwindsor.acare` (`apps/web/android`) | Sideloaded APK, published on GitHub Releases |
| Push notifications | Firebase Cloud Messaging, Firebase project `acare-uwindsor` | Firebase |
| Email | Resend (HTTPS) or SMTP, chosen by which variables are set | Provider account owned by the operator |
| CI/CD | GitHub Actions (`.github/workflows`) | GitHub |

`apps/mobile` is an **Expo prototype** (offline capture and an outbox sync). It is not
built or shipped by any workflow and no tablet runs it. The tablets run the
Capacitor app in `apps/web/android`.

The tablet app does not load its UI from Vercel. The UI is bundled in the APK and
updated over the air; only API calls go to the network.

## 2. How a change reaches users

```
push to dev  ─┬─ OTA workflow builds the web bundle and registers it with the API
              └─ (dev deploys are treated as releases; see section 8)

merge dev → main (pull request; main is protected)
   ├── Vercel rebuilds the web app
   ├── Render rebuilds and redeploys the API (Docker, auto-deploy on commit)
   └── OTA workflow publishes a new web bundle to tablets (picked up on next launch)

change under apps/web/android or capacitor.config.ts on main
   └── Release APK workflow builds a signed APK → GitHub Release apk-v<versionCode>
```

Never push straight to `main`: it deploys to production.

## 3. Accounts and ownership

Keep this table current. Do not put emails, passwords or tokens in this file.

| Service | What it holds | Notes |
|---|---|---|
| GitHub | Code, Actions secrets, Releases (APKs and OTA bundles) | The repo **must stay public**: tablets download OTA bundles from Release assets without logging in. |
| Render | The API service and its environment variables | Billing is paid by a separate university account. |
| Vercel | The web app | Hobby plan. |
| MongoDB Atlas | The database | |
| Firebase | Push (project `acare-uwindsor`) | Two artefacts: `google-services.json` (client, ships in the APK) and a service-account key (secret, held in Render). |
| Email provider | Outbound alerts | Confirm which is live: Resend or SMTP. |
| Android release keystore | Signs every APK | See section 6. Irreplaceable. |

The previous developer retains collaborator access to the GitHub repository by
choice. Rotate the credentials in section 7 if that ever needs to end.

## 4. Environment variables (API — set in Render)

Defaults are defined in `apps/api/app/config.py`; `apps/api/.env.example` is the template.

| Variable | Purpose |
|---|---|
| `MONGO_URI`, `MONGODB_DB_NAME` | Database connection and database name |
| `SECRET_KEY` | Signs login tokens. Changing it logs everyone out. |
| `CORS_ORIGINS` | Extra allowed web origins (comma-separated). `https://uwindsor-accs.vercel.app` and any `*.vercel.app` are allowed by default in `app/main.py`. |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` | First-boot super admin, created only if that email does not exist. If the password is empty, a random one is generated and printed once in the service log. Existing accounts are never modified. |
| `FCM_SERVICE_ACCOUNT_JSON` | Firebase service-account key, whole JSON as one value |
| `FCM_ANDROID_CHANNEL_ID` | Must match `CHANNEL_ID` in `apps/web/src/lib/push.ts` and `default_notification_channel_id` in Android `strings.xml` |
| `APP_UPDATE_TOKEN` | Shared secret CI presents to register an OTA bundle. **Must equal the GitHub secret of the same name.** Unset = publishing closed. |
| `APP_UPDATE_ENABLED` | `false` halts OTA delivery fleet-wide |
| `RESEND_API_KEY` or `SMTP_HOST/PORT/USERNAME/PASSWORD/USE_TLS` | Email transport. With neither, email runs in mock mode. |
| `DEFAULT_SENDER_EMAIL`, `ENABLE_EMAIL_NOTIFICATIONS` | Sender address and master switch |
| `RATE_LIMIT_*`, `WATER_QUALITY_*`, `NOTIFICATION_*`, `*_EXPIRY_WARNING_DAYS` | Tuning; see `config.py` |

Web (Vercel): `VITE_API_URL`, the API's public URL, baked in at build time.

## 5. Service settings

**Render** (web service, Docker): repo `<owner>/uwindsor-accs`, branch `main`, root
directory `apps/api`, Dockerfile `apps/api/Dockerfile`, auto-deploy on commit, no
pre-deploy command. The container's `CMD` runs `python -m app.seed` and then
uvicorn. `render.yaml` in the repo root mirrors this for reference; the live service
was created in the dashboard, not from that file. **Keep the service URL
unchanged**: it is baked into every installed APK (`MOBILE_API_URL`).

**Vercel**: framework Vite, root directory `apps/web`, build `npm run build`, output
`dist`, Node 24.x, production branch `main`, no custom domain. `apps/web/vercel.json`
rewrites all routes to `index.html`.

**GitHub Actions secrets** (repo settings): `MOBILE_API_URL`, `APP_UPDATE_TOKEN`,
`ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`,
`ANDROID_KEY_PASSWORD`, `GOOGLE_SERVICES_JSON` (optional). Values cannot be read
back from GitHub; `scripts/setup-ci-secrets.ps1` re-uploads them from a machine that
has the keystore and `.env.mobile`.

## 6. Android tablets

- Package name `ca.uwindsor.acare` must never change; it is what identifies the app.
- **The signing keystore is the one irreplaceable asset.** Android accepts updates
  only if they are signed by the same key as the installed app. If every copy is
  lost, all devices must uninstall and reinstall. Keep at least two encrypted
  backups outside the repo. Alias `acare`. Verify a copy with
  `keytool -list -v -keystore acare-release.jks -alias acare` and compare the
  SHA-256 fingerprint.
- **Frontend-only change** (`apps/web/src`, styles, assets): merge to `main`, the OTA
  workflow ships it; tablets update on next launch. No APK.
- **Native change** (plugin, permission, manifest, Gradle, `capacitor.config.ts`):
  bump `versionCode` (must increase every time) and `versionName` in
  `apps/web/android/app/build.gradle`, merge to `main`; the Release APK workflow builds,
  signs and verifies it. Install it over the old one; do not uninstall first.
  Afterwards raise `min_version_code` on the next OTA bundle if it needs the new shell.
- **Roll back a bad bundle:** re-activate the previous one through
  `POST /app-updates/bundles/<version>/activate` (chair or admin), or halt OTA with
  `APP_UPDATE_ENABLED=false` in Render.
- **Not yet verified after the handover:** the first APK built by the new owner's CI
  has not been installed on a tablet. Before giving any APK to staff, install it on
  one test tablet over the current release and confirm the app opens with its
  session intact.
- Full details, including live reload and push debugging: `apps/web/ANDROID.md`.

## 7. Rotating secrets

Do these in the same sitting where two places must match.

| Secret | Where to change | Effect |
|---|---|---|
| `SECRET_KEY` | Render env | Everyone logs in again |
| `APP_UPDATE_TOKEN` | Render env **and** GitHub secret | Mismatch makes the OTA workflow fail with 401 |
| Database password | Atlas → Database Access, then `MONGO_URI` in Render | API reconnects on redeploy |
| Firebase service-account key | Firebase → Service accounts → new key, paste into `FCM_SERVICE_ACCOUNT_JSON`, delete the old key in Google Cloud | Confirm with `GET /notifications/push-status` |
| Email key or password | Provider dashboard, then Render env | |
| Render deploy hook | Render service settings → Regenerate hook | |
| Keystore | **Cannot be rotated** without every device reinstalling | Protect it instead |

## 8. Things to know

- **`dev` is not a private staging branch.** A push to `dev` also publishes an OTA
  bundle to tablets, and `dev` work has been seen reaching the live database. Treat a `dev` push as a release.
- The API's startup migrations run against the live database on every deploy. Do a
  data check before pushing schema or index changes.
- Records such as census events, water-quality logs and audit entries are append-only
  by design; corrections are new entries.
- The Render free tier would sleep and miss notification sweeps; this service runs on
  a paid plan. If it is ever downgraded, the sweep (`NOTIFICATION_SWEEP_INTERVAL_MINUTES`)
  backfills on the next pass.
- Tests are in `apps/api/tests` (`python -m pytest` from `apps/api`, with MongoDB
  running locally). The test session fixes the super-admin password to a known value.
- The university's scanned source documents (PDFs) are deliberately not in the
  repository, which is public.

## 9. First-day checklist for a new owner

1. Clone the repo, follow `README.md`, and run the API and web app locally.
2. Sign in to each service in section 3 and confirm you can see it.
3. Confirm you hold the keystore and its passwords, with two backups.
4. Run the OTA workflow by hand (Actions → OTA bundle → Run workflow) and confirm it
   ends with "Registered and activated."
5. Open `<api-url>/docs` and check the API responds.
6. Read `apps/web/ANDROID.md` before touching anything under `apps/web/android`.
