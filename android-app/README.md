# PESH Enroll (Android)

An Android app for PESH staff to register learners **in person** at the training hub -- kids who
have no device, email or internet connection of their own. It works fully offline: a signup is
saved on the phone immediately and syncs to the server automatically once the phone has internet.
An admin can then issue those learners a single certificate covering all four courses from the
Django admin (see the main [README.md](../README.md#offline-learners--combined-certificates)).

## How it works

- **Staff log in** with their PESH account (must have "Staff status" checked in Django admin --
  see below). The app stores a login token, not the password.
- **Register a learner**: first name, last name, country of origin, age, grade, whether they're
  currently a student, and their school (only asked when "student" is on). Saving writes to a
  local database on the phone straight away -- no internet needed at that moment.
- **Sync**: a background job (WorkManager) sends saved learners to the server as soon as the
  phone has a network connection, and keeps retrying periodically if it doesn't. Each learner has
  a random ID generated on the phone, so a retried sync can never create a duplicate on the
  server.
- **Registered learners** screen shows every learner saved on this phone with its status --
  Pending, Synced, or Error (with the reason) -- and a manual "sync now" button.

## Requirements

- [Android Studio](https://developer.android.com/studio) (Koala/2024.1 or newer) with JDK 17,
  which it bundles.
- A device or emulator running Android 8.0 (API 26) or newer.

## Open and run it

1. Open the `android-app/` folder in Android Studio (not the repo root).
2. Let Gradle sync finish (first sync downloads dependencies; can take a few minutes). If the
   Gradle wrapper is missing or broken, Android Studio will offer to regenerate it -- accept that.
3. Run the `app` configuration on an emulator or a device connected over USB with debugging
   enabled.

The debug build points at `http://10.0.2.2:8000/api/` by default, which is how the Android
emulator reaches `localhost:8000` on the host machine -- i.e. the Django backend from
`docker compose up` in the parent project, run with the dev override so port 8000 is exposed:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up db backend
```
On a **physical phone**, `10.0.2.2` doesn't exist -- change the server address on the login screen
to your computer's LAN IP instead, e.g. `http://192.168.1.20:8000/api/` (phone and computer must
be on the same Wi-Fi). For the real deployed backend, use its HTTPS address.

## Creating a staff (mentor) login

Only accounts with **Staff status** can sign in to this app (this is what separates a mentor
account from an ordinary learner account on the website). An existing admin creates one:

1. Django admin -> **Accounts -> Users -> Add user**, or open an existing user.
2. Set an email and password, then check **Staff status** under Permissions. Superuser status is
   not needed.

## Project layout

```
app/src/main/java/rw/pesh/enroll/
  data/            Room database (local storage), Retrofit API client, the repository that ties them together
  sync/            WorkManager background sync (SyncWorker, scheduling)
  ui/              Jetpack Compose screens (Login, Register, Registered learners) and navigation
```

Kotlin, Jetpack Compose (Material 3), Room, Retrofit + Moshi, WorkManager. No dependency
injection framework -- `PeshApp` (the `Application` subclass) wires the few singletons together
by hand, which is enough for an app this size.

## Known limitations / next steps

- **Login token storage** uses plain `SharedPreferences`. Fine for an internal staff tool, but if
  this app will hold anything more sensitive later, switch to
  [`EncryptedSharedPreferences`](https://developer.android.com/topic/security/data) (androidx
  security-crypto).
- **Cleartext HTTP** is allowed (`usesCleartextTraffic="true"`) so the app can reach an `http://`
  dev server during setup. Before shipping a release build, point `DEFAULT_API_BASE_URL` (in
  `app/build.gradle.kts`) at an `https://` backend and remove that manifest attribute.
- **Release builds are unminified** (`isMinifyEnabled = false`). Turning on R8 later needs keep
  rules for Moshi's reflective adapters and Retrofit -- see the comment in `proguard-rules.pro`.
- **Launcher icon** is a plain placeholder (`res/drawable/ic_launcher.xml`) -- swap it for real
  branding art.
- **Attribution on sync**: if learner records saved under one mentor's login are still pending
  when a *different* mentor logs in on the same phone, the next sync sends them under whoever is
  currently logged in. Fine for how the hub actually works (one phone, whoever's on shift), but
  worth knowing.
- This project was written and code-reviewed without a device/emulator available in the
  environment that built it. See the note in the top-level project handoff for what was and
  wasn't verified.
