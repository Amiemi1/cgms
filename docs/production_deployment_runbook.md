# CGMS Production Deployment and Rollback Runbook

## Purpose

This runbook governs deployment of the Sprint 18 browser runtime. It covers
configuration validation, startup, smoke testing, operational acceptance and
rollback. It does not introduce a database migration framework or redefine
platform-wide health architecture.

## Canonical runtime

Deploy only:

```text
app.dashboard.main:app
```

The following are not approved production entry points:

```text
app.main:app
app.dashboard.routes.main:app
```

## Preconditions

Before deployment:

1. Record the release commit, branch and approval reference.
2. Confirm the repository is clean.
3. Confirm the full regression suite is green.
4. Complete `docs/deployment_checklist.md`.
5. Provision the database and verify a current backup.
6. Supply secrets through the approved deployment secret mechanism.
7. Configure HTTPS and reverse-proxy trust.
8. Run the production preflight in the target runtime environment.

The populated environment must never be copied into the repository,
validation output or release evidence.

## Required production configuration

Minimum controls:

```text
ENVIRONMENT=production
CGMS_SQL_ECHO=false
CGMS_DATABASE_STARTUP_POLICY=strict
DATABASE_URL=<managed secret>
CGMS_JWT_SECRET=<managed random secret>
CGMS_SESSION_COOKIE_NAME=__Host-cgms_session
CGMS_SESSION_EXPIRE_MINUTES=30
CGMS_CSRF_COOKIE_NAME=__Host-cgms_csrf
CGMS_CSRF_EXPIRE_SECONDS=600
CGMS_LOGIN_THROTTLE_WINDOW_SECONDS=900
CGMS_LOGIN_THROTTLE_PAIR_LIMIT=5
CGMS_LOGIN_THROTTLE_NETWORK_LIMIT=25
CGMS_LOGIN_THROTTLE_BLOCK_SECONDS=900
CGMS_LOGIN_THROTTLE_RETENTION_DAYS=7
```

`CGMS_ALLOWED_ORIGINS` may remain blank for same-origin browser access.
When configured, it must contain exact approved HTTPS origins.

`CGMS_TRUSTED_PROXY_CIDRS` must contain only the actual approved proxy
networks. Leave it blank when CGMS does not receive requests through a
trusted proxy.

A dedicated `CGMS_LOGIN_THROTTLE_SECRET` is recommended. When it is absent,
the current implementation derives the throttle HMAC key from
`CGMS_JWT_SECRET` using a domain-specific context.

## Preflight

Run in the same process environment used by the deployment:

```powershell
py -3.11 scripts/operations/production_preflight.py
```

Do not continue when the exit code is non-zero.

The preflight intentionally prints control names and outcomes only. It must
not be modified to print raw values.

## Database provisioning

CGMS currently initializes SQLModel metadata at application startup.

In staging and production:

- startup policy is strict;
- initialization failure prevents application startup;
- successful startup does not prove that a reversible migration plan exists.

The absence of a formal migration framework is a known residual risk.
Before a release that changes models:

1. compare model changes with the deployed schema;
2. create and test an explicit database change and rollback procedure;
3. capture a backup;
4. obtain separate approval when a migration framework or schema redesign is
   required.

## Application startup

Example Uvicorn command behind an approved TLS-terminating platform:

```powershell
py -3.11 -m uvicorn app.dashboard.main:app `
    --host 0.0.0.0 `
    --port 8000 `
    --proxy-headers `
    --forwarded-allow-ips "<approved proxy addresses>"
```

Use `--proxy-headers` and forwarded-address trust only when the deployment
network is explicitly controlled. CGMS login throttling separately enforces
`CGMS_TRUSTED_PROXY_CIDRS`.

For direct TLS termination at Uvicorn, certificate and private-key paths
must come from the deployment platform. Never commit private keys.

## Startup acceptance

Accept startup only when:

- the process remains running;
- the runtime reports the expected environment in controlled startup logs;
- database schema initialization succeeds;
- no secret, database URL or credential appears in logs;
- SQL statements and bound values are not echoed;
- the login page is reachable through the final HTTPS hostname.

The existing `/system/health` and `/system/environment` endpoints are
informational and are not authoritative readiness probes.

## Browser smoke validation

Use a dedicated non-personal test account where available.

Validate:

1. `GET /auth/login` returns `200`.
2. Invalid credentials return generic `401`.
3. Repeated invalid attempts produce `429` with `Retry-After`.
4. Correct credentials remain blocked during the active throttle.
5. A separate administrator pair remains available.
6. Successful login redirects to `/patent-readiness/dashboard`.
7. Session and CSRF cookies have:
   `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`.
8. Patent dashboard access respects administrator/operator/viewer roles.
9. Evidence export masking respects the active role.
10. Logout clears cookies and invalidates the persistent session.
11. Revoked sessions are rejected.
12. Fresh login-security events are privacy-safe and throttle keys remain
    pseudonymous.

Never place passwords, cookies, tokens, raw email addresses, raw IP
addresses, secrets or database URLs in the validation record.

## Security-header validation

For governed browser responses verify:

```text
Cache-Control: no-store
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Content-Security-Policy: <governed route policy>
```

## Operational monitoring

Minimum operational ownership:

- application process and restart owner;
- database availability and backup owner;
- security-log access owner;
- login-throttling incident owner;
- session-revocation owner;
- secret-rotation owner;
- release and rollback decision owner.

Current platform health routes must not be treated as synthetic monitoring
until dependency-aware readiness probes are separately designed and
approved.

## Rollback triggers

Initiate rollback when any of the following occurs:

- application startup fails after configuration correction;
- database initialization fails;
- browser authentication or authorization regresses;
- secure cookie attributes are missing;
- session revocation fails;
- login throttling fails open;
- raw credentials, secrets or identifiers enter logs;
- Patent dashboard or export permissions are incorrect;
- deployment error rate exceeds the approved release threshold.

## Application rollback

1. Stop new traffic to the affected release.
2. Preserve logs and security evidence.
3. Record the rollback decision and reason.
4. Redeploy the previous known-good image or commit.
5. Retain session, throttle and security-log tables unless incident response
   explicitly approves data removal.
6. Repeat the login, authorization, logout and revocation smoke tests.
7. Confirm that no secret was exposed during rollback.
8. Record the restored commit and timestamp.

## Database rollback limitation

`SQLModel.metadata.create_all()` is not a reversible migration mechanism.
Do not assume that application rollback reverses schema changes.

When schema changes are involved:

- stop deployment;
- preserve a backup;
- use the release-specific approved database rollback procedure;
- obtain separate architectural approval when no tested rollback exists.

## Post-deployment record

Record only non-secret evidence:

```text
Release commit:
Environment:
Deployment timestamp:
Preflight result:
Regression result:
Database initialization result:
HTTPS smoke result:
Authentication result:
Authorization result:
Revocation result:
Throttle result:
Audit privacy result:
Rollback reference:
Decision:
Reviewers:
Residual risks:
```
