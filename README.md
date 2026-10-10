# PESH website and online courses

React frontend, Django REST backend, PostgreSQL, all run with Docker. Courses: Microsoft Word, Microsoft Excel, Internet and AI, Scratch Programming.

```
frontend/   React (Vite) single-page app, served by nginx in production
backend/    Django + Django REST Framework (accounts, courses, certificates, MTN MoMo)
courses/    Source Word files for the curriculum
tools/      build_courses.py: Word files -> backend/courses/data/*.json
```

## Run everything (Docker)

```bash
cp .env.example .env        # then edit: at least POSTGRES_PASSWORD and DJANGO_SECRET_KEY
docker compose up --build
```

Open http://localhost:8080. The first start creates the database, imports the three courses and, if
`DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` are set in `.env`, creates an admin user.

- Site: http://localhost:8080
- Admin (edit courses and lessons, see payments and certificates): http://localhost:8080/admin/
- Stop: `docker compose down` (add `-v` to also delete the database)

## Develop with live reload

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up db backend   # API on :8000
cd frontend && npm install && npm run dev                                       # site on :5173
```

## Tests

```bash
docker compose exec backend sh -c "DJANGO_DEBUG=1 python manage.py test"   # backend (runs on Postgres)
cd frontend && npm test                                                     # frontend
```

## How it works

- **Login:** email + password, Django sessions (cookie) with CSRF protection. Password reset emails are printed in the
  backend log until you set `EMAIL_HOST` and friends in `.env`.
- **Progress:** stored per learner and lesson in Postgres. Lessons are identified by stable keys (`l1`, `l2`, ...).
- **Final exam:** every course has an online multiple-choice exam. It unlocks when all lessons are complete. Each attempt
  draws 20 random questions from the course's question bank (32-57 per course), shuffles the answer order, and has a
  30-minute timer that the server enforces. The pass mark is 70%. Learners can retake the exam as many times as they like
  (no waiting; an admin can set a wait per exam if wanted). After a fail they see their score and which questions they
  missed, but never the correct answers. Grading happens only on the server; the browser never receives the answers.
- **Certificate:** unlocks only when every lesson is complete **and the exam is passed** (the server checks both, so the
  payment API refuses otherwise). The learner then pays `CERTIFICATE_PRICE` (20,000 RWF, set on the
  server) with MTN MoMo. The server asks MoMo for the real payment status (by polling and by MoMo's callback) and only then
  issues the certificate. Each has a code such as `PESH-EXCE-1A2B3C4D`, a PDF download, and a public page at `/verify/<code>`.
- **Content:** edit lessons in the admin. Re-importing from the Word files with
  `docker compose exec backend python manage.py import_courses` overwrites edits, so use `--only-new` to keep them
  (the container does this automatically on start).

## Offline learners & combined certificates

Some learners take the courses in person at the hub, with no device, email or internet of their own. The
[`android-app/`](android-app/) folder is a separate Android app PESH staff use to register those learners --
it works with no internet (saves on the phone, syncs automatically once online) and asks for first name, last
name, country of origin, age, grade, and, only if they're currently a student, their school. See
[`android-app/README.md`](android-app/README.md) for how to build and run it, and how to create a staff login.

Once a learner has taken all four courses in person, an admin issues them **one certificate covering all four
courses** (there is no per-course tracking -- it's staff's call that the learner finished the program):

1. Django admin -> **Offline learners** -> select the learner(s) -> action **"Issue combined certificate"**.
2. Open the new entry under **Offline certificates** and click **Download PDF**.

The certificate has its own code (`PESH-ALL-XXXXXXXX`) and is checkable at the same public `/verify/<code>` page
as the regular per-course certificates. Backend pieces: the `offline_enrollment` Django app (models, the
staff-only mobile API at `/api/mobile/...`, the admin action) and `certificates/pdf.py`'s
`combined_certificate_pdf()`.

## Editing exams

In the admin, open **Exams**: change the pass mark, questions per attempt, time limit and retake wait, and add, edit or
switch off questions (each question has 2-6 options and the position of the right one, starting at 0). Set "Retake wait minutes" above 0 if you ever want a pause between attempts. The bundled
question banks were written from the lessons and live in `tools/build_exams.py`; review them with your teachers before
launch. After editing that file:

```bash
python3 tools/build_exams.py
docker compose up -d --build backend
docker compose exec backend python manage.py import_exams    # replaces the bank; --only-new keeps admin edits
```

### Word copies of the exams (for teacher review)

`exam-documents/` has one Word file per course with every question and a teacher answer key. To regenerate after
editing the questions in `tools/build_exams.py`:

```bash
python3 tools/build_exams.py --docs
cd tools && npm install docx && node make_exam_docs.js
```

## MTN MoMo setup

1. Sign up at https://momodeveloper.mtn.com, subscribe to **Collections**, copy the Primary key into `MOMO_SUBSCRIPTION_KEY`.
2. Create a sandbox API user and key (prints `MOMO_API_USER` and `MOMO_API_KEY`):
   ```bash
   docker compose run --rm backend python manage.py momo_sandbox_setup
   ```
3. Put the three values in `.env` and run `docker compose up -d backend`.
4. The sandbox only charges in EUR with test numbers, so no real money moves. For real RWF payments apply to MTN for
   production access, then set `MOMO_BASE_URL` (MTN gives you this), `MOMO_TARGET_ENVIRONMENT=production`, `MOMO_CURRENCY=RWF`
   and the production keys. When the site has a public https address, set `MOMO_USE_CALLBACK=1` so MoMo notifies the server
   as soon as a payment finishes.

## Deploy to a server

Any Linux server with Docker works (a small VPS is enough).

1. Point your domain at the server and put HTTPS in front of the `web` container (Caddy or an nginx/Traefik proxy that
   forwards to port 8080; Caddy does certificates automatically).
2. In `.env`: `DJANGO_DEBUG=0`, a long random `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=yourdomain.org`,
   `CSRF_TRUSTED_ORIGINS=https://yourdomain.org`, `SITE_URL=https://yourdomain.org`, `SECURE_COOKIES=1`,
   `BEHIND_HTTPS_PROXY=1`, a strong `POSTGRES_PASSWORD`, real SMTP settings, and change the admin password.
3. `docker compose up -d --build`.
4. Back up the `pgdata` Docker volume regularly (for example `docker compose exec db pg_dump -U pesh pesh > backup.sql`).

## Updating course content from the Word files

```bash
python3 tools/build_courses.py                       # regenerates backend/courses/data/*.json
docker compose up -d --build backend
docker compose exec backend python manage.py import_courses   # add --only-new to keep admin edits
```

Do not change lesson keys (`l1`, `l2`, ...) once learners have progress.

## Known limits

- The exam is online and unsupervised, so a learner could get help from someone else. The random question draw, timer
  and retake wait make sharing answers harder but do not stop it. For higher stakes, run the exam in person at the
  training center (learners can take it on the hub computers).
- The Excel Word file has blank spots where formulas should be. The build script fills in the ones the lesson text
  implies; "What is a Formula?" is still blank in the original.
- The Word file's "Writing and Creativity Competition" section is not a lesson and is not included.
