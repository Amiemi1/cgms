# Contextual Group Memory System

CGMS is an enterprise contextual-memory, intelligence and governance
platform. The canonical production ASGI application is:

```text
app.dashboard.main:app
```

Do not deploy `app.main:app` or `app.dashboard.routes.main:app` as the
production entry point. Those modules remain legacy or specialized
application surfaces and are not the governed Sprint 18 browser runtime.

## Runtime requirements

- Python 3.11
- PostgreSQL with the required CGMS schema
- Environment-provided application secrets
- HTTPS at the application boundary or an approved TLS-terminating proxy
- A supported `ENVIRONMENT` value:
  `development`, `test`, `staging` or `production`

The application must never be started in staging or production with:

- SQL echo enabled;
- a warning-only database startup policy;
- placeholder secrets;
- an unapproved wildcard or HTTP browser origin;
- untrusted forwarding headers;
- a development database credential.

## Local development

The repository `docker-compose.yml` is a local-development database
convenience only. It exposes PostgreSQL on the host and uses development
credentials. It is not a production deployment definition.

Start the local database:

```powershell
docker compose up -d db
```

Create a local `.env` from `.env.example`, replace the development
placeholders, and keep the populated file outside Git.

Run the canonical dashboard:

```powershell
py -3.11 -m uvicorn app.dashboard.main:app `
    --host 127.0.0.1 `
    --port 8000
```

For local HTTPS validation, use the separately managed development
certificate and key. Never commit or distribute private keys.

## Production preflight

Run the preflight from the same environment that will launch the
application:

```powershell
py -3.11 scripts/operations/production_preflight.py
```

The preflight prints variable names and control outcomes only. It does not
print environment values, credentials, secrets, database URLs, cookies or
tokens.

Exit codes:

- `0`: no blocking configuration failures;
- `1`: one or more production configuration failures.

Warnings require explicit operational review but do not by themselves
change the exit code.

## Tests

Focused production-documentation validation:

```powershell
py -3.11 -m pytest -q `
    tests/test_production_preflight.py
```

Full regression:

```powershell
py -3.11 -m pytest -q
```

The current FastAPI `on_event` and Starlette `TemplateResponse`
deprecation warnings are known legacy warnings. They are not acceptance
failures, but they remain technical debt.

## Deployment governance

Use the following governed documents:

- `docs/deployment_checklist.md`
- `docs/production_deployment_runbook.md`

The `/system/health` and `/system/environment` endpoints are currently
informational. They are not authoritative deployment-readiness probes
because they do not yet perform complete dependency verification.

## Security boundary

The Sprint 18 browser boundary includes:

- host-bound `Secure`, `HttpOnly`, `SameSite=Strict` session cookies;
- signed browser CSRF protection;
- database-backed session authorization and revocation;
- role-controlled Patent dashboard and evidence export;
- persistent pair and network login throttling;
- pseudonymous login-security identifiers;
- explicit CORS allowlisting;
- production fail-fast database startup;
- SQL echo disabled in staging and production.

Never log or expose:

- passwords or password hashes;
- JWTs, cookies or CSRF tokens;
- signing or throttling secrets;
- raw login email addresses or client IP addresses;
- production database URLs;
- private keys or certificates containing private material.
