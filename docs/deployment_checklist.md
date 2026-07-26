# CGMS Production Deployment Checklist

This checklist is an evidence gate. A checkbox may be marked only after the
named evidence has been produced and reviewed. It does not replace an
approved change record, release decision or incident plan.

## 1. Release identity and authorization

- [ ] Release commit and branch recorded.
- [ ] Release owner identified.
- [ ] Deployment window approved.
- [ ] Rollback owner identified.
- [ ] Expected user impact recorded.
- [ ] Outstanding risks and accepted exceptions recorded.
- [ ] Full regression suite is green.
- [ ] `git diff --check` is clean.
- [ ] Working tree contains no unreviewed files.

Evidence:

```text
Commit:
Branch:
Regression result:
Approval reference:
```

## 2. Canonical application boundary

- [ ] ASGI entry point is exactly `app.dashboard.main:app`.
- [ ] `ENVIRONMENT` is `staging` or `production`.
- [ ] The production preflight exits with code `0`.
- [ ] SQL echo is disabled.
- [ ] Database startup policy is strict.
- [ ] No legacy ASGI entry point is used.
- [ ] The current `/system/health` endpoint is not used as the sole
      readiness gate.
- [ ] The current `/system/environment` endpoint is not used as proof of
      deployment readiness.

## 3. Secrets and environment configuration

- [ ] `DATABASE_URL` is supplied through the approved secret mechanism.
- [ ] `CGMS_JWT_SECRET` is random, at least 32 characters and not a
      placeholder.
- [ ] A dedicated `CGMS_LOGIN_THROTTLE_SECRET` is configured or the
      documented JWT-secret fallback has been explicitly accepted.
- [ ] Secrets are absent from Git, build logs and deployment output.
- [ ] JWT issuer, audience and expiry are reviewed.
- [ ] Session and CSRF cookie names retain the `__Host-` prefix.
- [ ] Session and CSRF expiry values are within supported bounds.
- [ ] Secret-rotation and emergency-revocation owners are identified.

## 4. Network, TLS and proxy trust

- [ ] Public access is HTTPS only.
- [ ] TLS certificate validity and hostname coverage are verified.
- [ ] HTTP-to-HTTPS redirection is enforced outside CGMS where applicable.
- [ ] `CGMS_ALLOWED_ORIGINS` contains exact approved HTTPS origins only,
      or is blank for same-origin access.
- [ ] Wildcard credentialed CORS is absent.
- [ ] Trusted reverse-proxy CIDRs are explicitly configured.
- [ ] Untrusted forwarding headers are not relied upon.
- [ ] Direct application port exposure is restricted.
- [ ] Database network access is restricted to approved workloads.

## 5. Database and persistence

- [ ] Production database connectivity is verified.
- [ ] Database credentials are non-development credentials.
- [ ] Schema provisioning is executed and recorded.
- [ ] Browser-session table availability is verified.
- [ ] Browser-login throttle table availability is verified.
- [ ] Security-log persistence is verified.
- [ ] Backup completion and retention are verified.
- [ ] Restore procedure has a current test record.
- [ ] Rollback implications of schema changes are reviewed.

CGMS currently uses `SQLModel.metadata.create_all()` and does not have a
formal migration framework. This is a recorded residual risk and must not
be represented as migration-safe deployment automation.

## 6. Browser authentication and authorization

- [ ] Login page returns HTTPS `200`.
- [ ] Invalid credentials return generic `401`.
- [ ] Repeated invalid attempts produce `429`.
- [ ] `Retry-After` is present on throttled responses.
- [ ] Correct credentials remain rejected during an active block.
- [ ] Administrator pair isolation is verified.
- [ ] Successful login redirects to the governed Patent dashboard.
- [ ] Session cookie is `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`.
- [ ] CSRF cookie is `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`.
- [ ] Logout invalidates the persistent session and clears browser cookies.
- [ ] Revoked sessions cannot regain access.
- [ ] Viewer, operator and administrator access boundaries are verified.
- [ ] Bearer headers and role headers cannot elevate browser access.

## 7. Response security and privacy

- [ ] Sensitive browser responses use `Cache-Control: no-store`.
- [ ] `X-Content-Type-Options: nosniff` is present.
- [ ] `X-Frame-Options: DENY` is present.
- [ ] `Referrer-Policy: no-referrer` is present.
- [ ] The governed Content Security Policy is present.
- [ ] Login-security audit events contain no raw email address or IP address.
- [ ] Throttle keys are pseudonymous.
- [ ] Passwords, tokens, cookies, secrets and database URLs are absent from
      application logs.

## 8. Operations and observability

- [ ] Application startup and shutdown events are visible.
- [ ] Database startup failure causes staging/production startup failure.
- [ ] Authentication failure, throttle and success events are persisted.
- [ ] Session-revocation events are persisted.
- [ ] Log retention and access controls are approved.
- [ ] Alert ownership and escalation routes are recorded.
- [ ] The deployment team understands that current health endpoints are
      informational rather than authoritative.
- [ ] Incident response contacts are current.

## 9. Smoke test and release decision

- [ ] Login page smoke test passed.
- [ ] Administrator login passed.
- [ ] Operator login passed.
- [ ] Viewer denial boundary passed.
- [ ] Patent dashboard access passed.
- [ ] Evidence export masking passed.
- [ ] Logout and revocation passed.
- [ ] Throttling and audit privacy passed.
- [ ] No secret or credential was included in the validation record.
- [ ] Release owner approved deployment continuation.

## 10. Rollback readiness

- [ ] Previous known-good image or commit is identified.
- [ ] Rollback command or platform action is documented.
- [ ] Database rollback limitation is understood.
- [ ] Session and throttle records will be preserved unless an approved
      incident action requires otherwise.
- [ ] Rollback verification tests are identified.
- [ ] Communications owner is assigned.

## 11. Final approval

```text
Release commit:
Environment:
Deployment owner:
Security reviewer:
Operations reviewer:
Rollback reference:
Decision: APPROVED / REJECTED
Decision timestamp:
Residual risks:
```
