# Phase 3: Auth, Dashboard, Testing, and Production Readiness

## Completed

- Added JWT authentication with register, login, guest sessions, and `/api/v1/auth/me`.
- Added secure password hashing using `pbkdf2_sha256`.
- Added user-aware conversation history and authorization checks for conversation access.
- Protected admin knowledge operations: ingest, reindex, and delete document.
- Added frontend login/register/guest page.
- Added frontend control center for analytics, document inspection, ingestion, and reindex operations.
- Fixed router structure so the browser app uses a single `BrowserRouter`.
- Added API client bearer-token handling with local storage.
- Added backend tests for auth and admin protection.
- Added GitHub Actions CI for backend tests and frontend production build.
- Updated final build documentation and environment examples.

## New API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create user and return JWT |
| POST | `/api/v1/auth/login` | Authenticate existing user |
| POST | `/api/v1/auth/guest` | Create guest account/session |
| GET | `/api/v1/auth/me` | Return current user |

## Frontend Routes

| Route | Purpose |
|-------|---------|
| `/` | Chat workspace |
| `/login` | Login, register, guest entry |
| `/dashboard` | Analytics and admin operations |

## Verification

- Backend tests: 8 passing
- Frontend production build: passing

## Notes

The first registered account becomes `admin`, which can run ingestion and reindex operations. Later accounts default to `user`, while guest sessions use the `guest` role.
