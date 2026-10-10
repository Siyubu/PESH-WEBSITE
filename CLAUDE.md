# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PESH (Rwanda digital-skills nonprofit) website plus an online learning platform: React frontend, Django REST backend, PostgreSQL, all run with Docker, and a separate Android staff app for registering offline learners. See `README.md` for setup, MoMo, and deployment details.

## Commands

```bash
cp .env.example .env && docker compose up --build        # full stack on http://localhost:8080 (admin at /admin/)

# Dev loop: API on :8000 (source mounted, runserver), React on :5173 (proxies /api, /admin to :8000)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up db backend
cd frontend && npm install && npm run dev

# Backend tests (the prod compose image bakes code in at build time, so exec tests only see the last build)
docker compose exec backend sh -c "DJANGO_DEBUG=1 python manage.py test"
docker compose exec backend sh -c "DJANGO_DEBUG=1 python manage.py test exams.tests.ExamFlowTests.test_pass_with_all_correct"   # single test
# Test against your working tree without rebuilding:
docker run --rm -e DJANGO_DEBUG=1 -v "$PWD/backend":/app -w /app python:3.12-slim sh -c "pip install -q -r requirements.txt && python manage.py test"

# New models/apps need migrations (generate with the same container trick, then rebuild)
docker compose exec backend python manage.py makemigrations <app>

cd frontend && npm test                      # vitest
cd frontend && npx vitest run src/api.test.js   # single file

cd android-app && ./gradlew :app:assembleDebug   # needs an Android SDK; Gradle 8.7 needs JDK 17-21 (NOT 25)
```

Gotchas:
- Settings refuse to start without `DJANGO_SECRET_KEY` unless `DJANGO_DEBUG=1`. With no `POSTGRES_HOST` they fall back to SQLite.
- The Android emulator reaches the host at `10.0.2.2`, which must be in `DJANGO_ALLOWED_HOSTS` or Django answers 400.
- `docker-compose.dev.yml` mounts `./backend` over `/app`, so `backend/entrypoint.sh` must be executable (`chmod +x`) or the container crash-loops with "permission denied".
- DRF throttles use the shared cache; tests that hit throttled endpoints call `cache.clear()` in `setUp`.

## Architecture

**Backend** (`backend/`, apps wired in `config/settings.py` and `config/urls.py`): `accounts` (custom email-login `User`, session auth), `courses` (Course/Lesson/LessonProgress), `exams`, `certificates` (payments + PDFs), `offline_enrollment` (mobile API). Only `config.urls` mounts routes; most APIs live under `/api/<app>/`, certificates and offline_enrollment under `/api/`.

**Auth model**: web uses Django session cookies with CSRF. Anonymous auth endpoints (login/register/reset) use `accounts.authentication.StrictCsrfSessionAuthentication` because stock DRF skips CSRF for anonymous requests. The frontend (`src/api.js`) reads the `csrftoken` cookie, which `/api/auth/session/` sets on load. The Android app instead uses DRF `authtoken` via `/api/mobile/login/`, which only accepts `is_staff` users.

**Content pipeline** (source of truth is the Word files, not the DB):
- `courses/*.docx` -> `tools/docx_blocks.py` (stdlib docx reader) + `tools/build_courses.py` -> `backend/courses/data/*.json` -> `manage.py import_courses` (the container entrypoint runs it with `--only-new`, so admin edits are never overwritten).
- Lesson `key`s (`l1`, `l2`, ...) are stable IDs that learner progress references; never renumber them. Lesson bodies are JSON block lists rendered as plain text by `LessonBody.jsx` (no HTML injection).
- `build_courses.py` patches blank Excel formulas that are missing in the source docx.
- Exam questions are authored in `tools/build_exams.py` (not JSON) -> `backend/exams/data/*.json` -> `manage.py import_exams` (matches by question text, updates in place, retires removed questions). The script asserts the correct answer is not the longest option too often; keep wrong options similar in length (`BALANCED_WRONG`). `build_exams.py --docs` + `tools/make_exam_docs.js` regenerate the teacher Word files in `exam-documents/`.

**Certificate rules** (`certificates/services.py`): eligibility = every lesson complete AND exam passed (`exams.services.has_passed`). The price is set server-side (`CERTIFICATE_PRICE`), never from the client. A certificate is issued only after the server asks MTN MoMo for the real status and the amount matches (`sync_payment`); the MoMo callback body is ignored and just triggers that re-check. The frontend polls `/api/certificates/<slug>/status/`. MoMo sandbox only supports EUR; `MOMO_CURRENCY` must be RWF in production. PDFs are drawn with reportlab in `certificates/pdf.py`. `/api/certificates/verify/<code>/` looks up both `Certificate` and `OfflineCertificate`.

**Exams** (`exams/services.py`): grading is server-side only. `ExamAttempt.layout` stores the shuffled option order per question; the API never returns `correct_index` or explanations, and the review after submit shows only the learner's own wrong answers. Retakes are unlimited (`retake_wait_minutes` default 0); the time limit is enforced server-side with a grace window.

**Offline enrollment**: staff register learners in the Android app (`android-app/`, Kotlin/Compose/Room/WorkManager). Saves go to local Room first and sync later. `POST /api/mobile/offline-learners/` is idempotent on the phone-generated `client_id` and handles the concurrent-duplicate `IntegrityError` race (periodic and on-save sync workers can fire together). An admin action in Django admin ("Issue combined certificate") creates one `OfflineCertificate` listing all published courses; its PDF is at `/api/offline-certificates/<code>/pdf/` (staff only). In the app, a 401 from sync logs the device out; default WorkManager init is disabled in the manifest so `PeshApp` can supply a custom `WorkerFactory`.

**Frontend** (`frontend/`): Vite + React 18 + react-router v6, no UI library; styles are plain CSS (`site.css` from the original static site, `learn.css`, `extra.css`). `Layout.jsx` toggles `body.learn` to switch between the marketing look and the dark learning theme. Vite proxies `/api`, `/admin`, `/static` to the backend in dev; `frontend/nginx.conf` does the same in the container and serves the SPA fallback.
