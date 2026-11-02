# PESH Enroll (Android)

An Android app for PESH staff to register learners **in person** at the training hub -- kids who
have no device, email or internet connection of their own. It works fully offline: a signup is
saved on the phone immediately and syncs to the server automatically once the phone has internet.
An admin can then issue those learners a single certificate covering all four courses from the
Django admin (see the main [README.md](../README.md#offline-learners--combined-certificates)).

## How it works

- **Staff log in** with their PESH account (must have "Staff status" checked in Django admin --
  see below). The app stores a login token, not the password. **A login lasts 24 hours**: after
  that the server refuses it, the app signs out and says so, and the mentor signs in again. Learners
  saved on the phone are kept and are sent as soon as the new login succeeds.
- **Register a learner**: first name, last name, country of origin (pick from a searchable list),
  date of birth (calendar; the age is shown under it), and whether they're currently a student.
  Grade and school are only asked when "student" is on. Saving writes to a local database on the
  phone straight away -- no internet needed at that moment.
- **Correct a mistake**: open **Registered learners** and tap a learner. The edit screen is the same
  form, pre-filled. Saving marks it Pending and the next sync updates the server's copy (it does not
  create a duplicate). If an older version of a record arrives late, the server ignores it, so an edit
  can't be undone by a slow sync.
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

## Releasing to real phones

The phones need a server on the internet (see "Deploy to a server" in the [main README](../README.md)), because
Android only lets a release app talk to an `https://` address. Then:

1. **Signing key (once).** `release.keystore` and `keystore.properties` in this folder are your app's identity.
   They are git-ignored on purpose. **Back both up somewhere safe and private** (password manager or encrypted
   drive). If they are lost you can never publish an update that installs over the existing app; every phone
   would have to uninstall first, losing any learners not yet synced. To make a new key if you ever need one:
   `keytool -genkeypair -keystore release.keystore -alias pesh-enroll -keyalg RSA -keysize 2048 -validity 10000`
   and put the passwords in `keystore.properties` (`storeFile`, `storePassword`, `keyAlias`, `keyPassword`).
2. **Build** the signed app, giving it your server address (the build refuses to continue without it, or with
   a non-https one):
   ```bash
   cd android-app
   ./gradlew :app:assembleRelease -PPESH_API_BASE_URL=https://your-domain/api/
   ```
   The file is `app/build/outputs/apk/release/app-release.apk`. Android Studio's JDK 17 and SDK work fine; from a
   terminal set `JAVA_HOME` to a JDK 17-21 and `ANDROID_HOME` to the SDK.
3. **Updating later:** raise `versionCode` (a whole number, +1 each release) and `versionName` in
   `app/build.gradle.kts`, rebuild with the same key, and install the new APK over the old one. Learners saved on
   the phone are kept.

**Installing on a phone (no app store).** Send `app-release.apk` to the phone (USB cable, WhatsApp/email to
yourself, or a download link), open it, and allow "Install unknown apps" for the app you opened it with when
Android asks. Then sign in with a staff account (Staff status ticked in the website's admin). Keep the APK
private: anyone who has it can install the app, though only staff accounts can log in.

**Google Play instead.** Play wants an app bundle (`./gradlew :app:bundleRelease -P...`), a developer account
(one-time fee), and a recent `targetSdk`; this project currently targets 34, which Play no longer accepts for new
apps, so that would mean raising it and retesting. For a handful of staff phones, installing the APK directly is
simpler.

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
- **HTTP vs HTTPS**: only debug builds (run from Android Studio) may use plain `http://`, to reach your computer
  during development. Release builds are HTTPS-only.
- **No cloud backup**: `allowBackup` is off, so Android does not copy the phone's learner data or login to a
  Google account. Moving to a new phone means installing the app fresh and re-registering anything not yet synced
  first (sync before swapping phones).
- **Release builds are unminified** (`isMinifyEnabled = false`), which is fine for an internal app. Turning on R8 later needs keep
  rules for Moshi's reflective adapters and Retrofit -- see the comment in `proguard-rules.pro`.
- **Launcher icon** is a plain placeholder (`res/drawable/ic_launcher.xml`) -- swap it for real
  branding art.
- **One account, one phone at a time**: each login issues a new token and retires the previous one, so
  signing in with the same staff account on a second phone signs the first one out (its saved learners
  stay put and sync after it logs in again).
- **Upgrading from the first version**: the phone's database is migrated automatically. Learners saved
  before the update only had an age, so they get an estimated date of birth (1 January of the birth
  year). Correct them with the edit screen if the exact date matters.
- **Attribution on sync**: if learner records saved under one mentor's login are still pending
  when a *different* mentor logs in on the same phone, the next sync sends them under whoever is
  currently logged in. Fine for how the hub actually works (one phone, whoever's on shift), but
  worth knowing.
- This project was written and code-reviewed without a device/emulator available in the
  environment that built it. See the note in the top-level project handoff for what was and
  wasn't verified.
