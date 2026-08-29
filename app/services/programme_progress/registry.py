from __future__ import annotations

from copy import deepcopy
from typing import Any, Final

from app.services.programme_progress.commercial_value import (
    build_commercial_value_view,
)


_PROGRAMME_PROGRESS: Final[dict[str, Any]] = {
    "page": {
        "title": "CGMS Programme Progress Dashboard",
        "subtitle": (
            "Authoritative delivery, validation, governance, "
            "dashboard-access and startup register."
        ),
        "as_of": "25 August 2026",
        "current_sprint": "Sprint 22",
        "current_work": "CAP-004 Step 264T / Readiness-Currency Closure",
        "status": (
            "Step 264S readiness reassessment passed; Step 264T records "
            "CAP-004 as Implemented / PILOT_READY with P0 priority "
            "retained and the commercial blocker closed"
        ),
        "branch": "cgms-v2-roadmap",
        "canonical_record": (
            "docs/CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md"
        ),
    },
    "summary": [
        {
            "label": "Current milestone",
            "value": "CAP-004 Step 264T",
            "detail": (
                "Step 264S readiness reassessment passed and Step 264T "
                "records CAP-004 as PILOT_READY, closes its commercial "
                "blocker and preserves publication as a separate boundary"
            ),
        },
        {
            "label": "Current regression suite",
            "value": "696 passed",
            "detail": (
                "Complete Step 264R regression passed against isolated "
                "PostgreSQL 16.14 / pgvector 0.8.6 with 37 known "
                "non-blocking deprecation warnings"
            ),
        },
        {
            "label": "Step 264R technical validation",
            "value": "696 + PostgreSQL PASS",
            "detail": (
                "Four governed migrations applied in order and skipped "
                "idempotently on rerun; append-only UPDATE/DELETE "
                "enforcement passed; complete regression recorded "
                "696 passed with 37 warnings"
            ),
        },
        {
            "label": "Latest published checkpoint",
            "value": "6a51c09",
            "detail": (
                "Published Step 264O governance closure baseline; "
                "current CAP-004 Step 264Q-264T work remains "
                "unstaged and unpublished"
            ),
        },
        {
            "label": "GitHub Actions",
            "value": "Run #41 — Success",
            "detail": (
                "Latest published Product Readiness CI passed for "
                "correction commit fe313621; published governance "
                "baseline subsequently closed at 6a51c095"
            ),
        },
        {
            "label": "Runtime contracts",
            "value": "PASS",
            "detail": (
                "Effective /dashboard/next-action/{chat_id} GET route "
                "is unique and authorization inventory is aligned to "
                "the corrected production route surface"
            ),
        },
        {
            "label": "Pilot readiness",
            "value": "NOT READY",
            "detail": (
                "CAP-004 commercial blocker is closed after the Step 264S "
                "PASS determination and Step 264T promotion; CAP-005 "
                "remains the unresolved P0 commercial blocker and the "
                "pilot verdict remains NOT READY"
            ),
        },
    ],
    "executive_value": build_commercial_value_view(),
    "navigation": [
        {
            "title": "Programme Progress",
            "path": "/progress",
            "description": (
                "Delivery history, validation evidence, "
                "startup commands and navigation."
            ),
            "access": "view_dashboard",
            "local_url": (
                "https://127.0.0.1:8443/progress"
            ),
        },
        {
            "title": "Memory and Intelligence Workspace",
            "path": "/dashboard",
            "description": (
                "Memory, insights, next-best-action, "
                "runtime feeds and priority tasks."
            ),
            "access": "Application route",
            "local_url": (
                "https://127.0.0.1:8443/dashboard"
            ),
        },
        {
            "title": "Runtime Operator Console",
            "path": "/operator",
            "description": (
                "Runtime status, operational actions "
                "and event timeline."
            ),
            "access": "Application route",
            "local_url": (
                "https://127.0.0.1:8443/operator"
            ),
        },
        {
            "title": "Product Readiness Dashboard",
            "path": "/product-readiness/dashboard",
            "description": (
                "Capability assessment, readiness profile "
                "and engineering recommendations."
            ),
            "access": "Application route",
            "local_url": (
                "https://127.0.0.1:8443/"
                "product-readiness/dashboard"
            ),
        },
        {
            "title": "Patent and IP Progress Dashboard",
            "path": "/patent-readiness/dashboard",
            "description": (
                "Patent filing, evidence, innovation, "
                "claims and governance status."
            ),
            "access": "view_patent_governance",
            "local_url": (
                "https://127.0.0.1:8443/"
                "patent-readiness/dashboard"
            ),
        },
        {
            "title": "Secure Browser Sign In",
            "path": "/auth/login",
            "description": (
                "Authenticated entry point for protected "
                "browser dashboards."
            ),
            "access": "Public authentication page",
            "local_url": (
                "https://127.0.0.1:8443/auth/login"
            ),
        },
    ],
    "foundations": [
        {
            "title": "Runtime",
            "status": "Complete",
        },
        {
            "title": "Observability",
            "status": "Complete",
        },
        {
            "title": "Workspace",
            "status": "Complete",
        },
        {
            "title": "Memory Engine",
            "status": "Complete",
        },
        {
            "title": "Memory Intelligence",
            "status": "Complete",
        },
        {
            "title": "Enterprise Event Bus",
            "status": "Complete",
        },
    ],
    "current_focus": [
        "CAP-004 Step 264S readiness reassessment passed",
        "CAP-004 Step 264T Implemented / PILOT_READY currency recorded",
        "696-test PostgreSQL 16 / pgvector complete regression remains green",
        "CRG-001 CAP-004 commercial blocker closed; CAP-005 remains P0",
        "Product Readiness 27% / pilot-scope readiness 35%",
    ],
    "upcoming": [
        "Separate approval required before Step 264U CAP-004 closure publication",
        "No staging, commit or push authorised by Step 264T",
        "CAP-005 and remaining P1 commercial blockers remain separately governed",
    ],
    "sprints": [
        {
            "id": "SPRINT-16",
            "title": "Sprint 16 - Product Readiness Engine",
            "status": "Complete and remotely validated",
            "status_class": "complete",
            "summary": (
                "The Product Readiness Engine, dashboard, production "
                "capability bootstrap and repository-managed CI gate "
                "are implemented and remotely validated."
            ),
            "milestones": [
                {
                    "id": "PRE-001",
                    "title": "Capability Registry",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-002",
                    "title": "Scoring Engine",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-003",
                    "title": "Assessment Engine",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-004",
                    "title": "Recommendation Engine",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-005",
                    "title": "Product Readiness REST API",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-006",
                    "title": "Product Readiness Dashboard",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-006A",
                    "title": (
                        "Production Capability Bootstrap"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PRE-007",
                    "title": (
                        "Product Readiness CI/CD Integration"
                    ),
                    "status": (
                        "Complete — remote validation passed"
                    ),
                    "status_class": "complete",
                },
            ],
        },
        {
            "id": "SPRINT-17",
            "title": "Sprint 17 - Patent and IP Governance",
            "status": "Complete",
            "status_class": "complete",
            "summary": (
                "The governed patent domain, filing registry, "
                "evidence register, innovation map, dashboard, "
                "security boundary and export package are complete."
            ),
            "milestones": [
                {
                    "id": "PIP-001",
                    "title": "Patent Governance Domain Model",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PIP-002",
                    "title": (
                        "Filing and Administrative "
                        "Milestone Registry"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PIP-003",
                    "title": "Patent Evidence Register",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PIP-004",
                    "title": (
                        "Innovation and Claim-Expansion Map"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PIP-005",
                    "title": "Patent and IP Progress Dashboard",
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PIP-006",
                    "title": (
                        "Authentication and "
                        "Confidentiality Controls"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "PIP-007",
                    "title": (
                        "Exportable Patent Evidence Package"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
            ],
        },
        {
            "id": "SPRINT-18",
            "title": (
                "Sprint 18 - Secure Browser Access "
                "and Session Management"
            ),
            "status": "Complete and production-validated",
            "status_class": "complete",
            "summary": (
                "Secure browser authentication, persistent "
                "sessions, authorization revalidation, "
                "throttling, runtime hardening and production "
                "operational validation are complete."
            ),
            "milestones": [
                {
                    "id": "SBA-FOUNDATION",
                    "title": (
                        "Canonical roles and browser-session "
                        "security foundation"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "SBA-001D",
                    "title": (
                        "Secure Browser Login and Logout"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "SBA-003",
                    "title": (
                        "Server-Side Authorization Revalidation"
                    ),
                    "status": "Complete",
                    "status_class": "complete",
                },
                {
                    "id": "SBA-004",
                    "title": (
                        "Persistent Browser Session Revocation"
                    ),
                    "status": (
                        "Complete and production-validated"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "SBA-005",
                    "title": (
                        "Browser Patent Dashboard "
                        "and Export Migration"
                    ),
                    "status": (
                        "Complete and production-validated"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "SBA-005-UI",
                    "title": "Patent Dashboard UI Polish Addendum",
                    "status": (
                        "Complete and production-validated"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "SBA-006",
                    "title": (
                        "Authentication Throttling, Logging "
                        "and Failure Controls"
                    ),
                    "status": (
                        "Complete and production-validated"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "SBA-007A",
                    "title": "Production Runtime Hardening",
                    "status": (
                        "Complete and regression-validated"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "SBA-007B",
                    "title": (
                        "Production Documentation "
                        "and Operational Validation"
                    ),
                    "status": (
                        "Complete, validated and published"
                    ),
                    "status_class": "complete",
                },
            ],
        },
        {
            "id": "SPRINT-19",
            "title": (
                "Sprint 19 - Programme Progress "
                "and Navigation"
            ),
            "status": "Complete and production-validated",
            "status_class": "complete",
            "summary": (
                "PRG-001 was explicitly approved as a "
                "Recommended Deviation under EG-001."
            ),
            "milestones": [
                {
                    "id": "PRG-001",
                    "title": (
                        "CGMS Programme Progress Dashboard"
                    ),
                    "status": (
                        "Complete, production-validated, "
                        "committed, and published"
                    ),
                    "status_class": "complete",
                },
            ],
        },

        {
            "id": "SPRINT-20",
            "title": (
                "Sprint 20 - Commercial Readiness "
                "Gap Assessment"
            ),
            "status": (
                "Complete, regression-validated, "
                "committed, and published"
            ),
            "status_class": "complete",
            "summary": (
                "CRG-001 reassessed all 20 P0 and P1 "
                "capabilities using repository, database, "
                "test, HTTPS and operational evidence."
            ),
            "milestones": [
                {
                    "id": "CRG-001",
                    "title": (
                        "CGMS Commercial Readiness "
                        "Gap Assessment"
                    ),
                    "status": (
                        "Complete, regression-validated, "
                        "committed, and published; "
                        "pilot verdict NOT READY"
                    ),
                    "status_class": "complete",
                },
            ],
        },
        {
            "id": "SPRINT-22",
            "title": (
                "Sprint 22 - Persistent Workspace "
                "Isolation Foundation"
            ),
            "status": (
                "CAP-003 closure published; CAP-004 Step 264T readiness "
                    "currency complete; publication pending separate approval"
            ),
            "status_class": "active",
            "summary": (
                "PWI-001 Step 187F completed integrated cross-workspace "
                "isolation validation across Bearer and persistent browser "
                "transports, migration integrity, complete regression and "
                "effective route uniqueness. Publication remains pending "
                "separate explicit approval."
            ),
            "milestones": [
                {
                    "id": "PWI-001-187C",
                    "title": "Workspace-Bound Authentication Principals",
                    "status": (
                        "Complete, validated, published "
                        "and reconciled"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "PWI-001-187D",
                    "title": (
                        "Tenant Persistence and "
                        "Query-Contract Integration"
                    ),
                    "status": (
                        "Complete, database-validated, canonically "
                        "closed, committed and published"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "PWI-001-187E",
                    "title": "Active Browser Workspace Switching",
                    "status": (
                        "Complete, validated, canonically closed, "
                        "committed and published"
                    ),
                    "status_class": "complete",
                },
                {
                    "id": "PWI-001-187F",
                    "title": (
                        "Cross-Workspace Isolation and "
                        "Integrated Closure"
                    ),
                    "status": (
                        "Technical closure complete and validated; "
                        "governance currency recorded; publication pending"
                    ),
                    "status_class": "active",
                },
            ],
        },
    ],
    "validation": [
        {
            "title": "CAP-004 Step 264T readiness-currency closure",
            "result": "PASS — PILOT_READY",
            "detail": (
                "Step 264S reassessment determined CAP-004 eligible for "
                "promotion; Step 264T records Implemented / PILOT_READY, "
                "retains P0 priority, closes the CAP-004 CRG-001 commercial "
                "blocker, recalculates Product Readiness to 27% and "
                "pilot-scope readiness to 35%, and retains NOT READY "
                "as the commercial pilot verdict"
            ),
        },
        {
            "title": "CAP-004 Step 264R isolated PostgreSQL validation",
            "result": "PASS — 696 passed",
            "detail": (
                "PostgreSQL 16.14 / pgvector 0.8.6; four governed "
                "migrations applied in order and skipped idempotently "
                "on immediate rerun; append-only UPDATE/DELETE "
                "enforcement passed; complete regression recorded "
                "696 passed with 37 warnings; disposable container "
                "removed and localhost port 55440 released"
            ),
        },
        {
            "title": "PWI-001 Step 187F integrated technical closure",
            "result": "PASS — publication pending",
            "detail": (
                "Duplicate next-action route corrected; authorization "
                "inventory aligned; CI schema bootstrap registers all 18 "
                "governed SQLModel tables; 59 focused closure tests passed; "
                "full isolated PostgreSQL 16 / pgvector regression recorded "
                "679 passed with 37 warnings; both PWI migrations applied "
                "in order and validated idempotently; live Bearer and "
                "persistent-browser cross-workspace separation passed; "
                "effective /dashboard/next-action/{chat_id} GET "
                "registration count is one"
            ),
        },
        {
            "title": "Product Readiness CI recovery closure",
            "result": "PASS — GitHub Actions",
            "detail": (
                "Recovery commit "
                "6b8a00dcc9ad597038a423591dd8aaf731593fa5; "
                "GitHub Actions run #34 succeeded in 7m 21s; "
                "local CI-equivalent regression recorded 651 passed "
                "with 37 warnings, JUnit recorded zero failures, "
                "zero errors and zero skipped, and the Product "
                "Readiness gate passed"
            ),
        },
        {
            "title": "CI database bootstrap",
            "result": "PASS",
            "detail": (
                "pgvector/pgvector:pg16 enabled the vector extension; "
                "Step 187F corrected CI model registration for learning "
                "and message, producing all 18 governed SQLModel tables "
                "before regression execution"
            ),
        },
        {
            "title": "PWI-001 Step 187E controlled publication",
            "result": "Complete — published",
            "detail": (
                "Commit 0140d4a26d2e814879c7e5c4a74451cf18f85d92; "
                "7 committed paths; 18 focused contracts and 52 selected "
                "non-database regressions green; 116-route governed "
                "surface preserved"
            ),
        },
        {
            "title": "PWI-001 Step 187D controlled publication",
            "result": "Complete — published",
            "detail": (
                "Commit cc366edd5d707ccebba065f46414a751b1e4b1e6; "
                "633 passed, 37 warnings; 59 committed paths; "
                "116-route governed surface preserved"
            ),
        },
        {
            "title": "PWI-001 Step 187D governance approval",
            "result": "Approved — not started",
            "detail": (
                "Approved as Planned Work within the existing approved PWI-001 Mandatory Architectural Intervention."
            ),
        },
        {
            "title": "PWI-001 Step 187C repository publication",
            "result": "Synchronized",
            "detail": (
                "Published commit chain: implementation "
                "05dcb2d0feba9bd0ad7c08fd8455302c183cec5a; canonical closure "
                "4624bf8c4c2944c3a8d05232b4565f3d5ed77e00; final reconciliation "
                "595de8fcd5c645a26c4c020028a750a6ee36bffc. Local, tracked upstream "
                "and direct remote cgms-v2-roadmap references "
                "matched at the final reconciliation commit."
            ),
        },
        {
            "title": "PWI-001 Step 187C runtime contracts",
            "result": "PASS",
            "detail": (
                "No routes were added or removed and no "
                "Step 187D, Step 187E or Step 187F behaviour "
                "was introduced."
            ),
        },
        {
            "title": "PWI-001 Step 187C complete regression",
            "result": "596 passed",
            "detail": "Complete CGMS regression passed with 37 warnings.",
        },
        {
            "title": "PWI-001 Step 187C authentication suite",
            "result": "218 passed",
            "detail": (
                "Authentication-focused regression passed with "
                "30 warnings."
            ),
        },
        {
            "title": "CRG-001 repository publication",
            "result": "Synchronized",
            "detail": (
                "Local, tracked remote and direct remote "
                "cgms-v2-roadmap references matched at "
                "16a673d80091d72f011ce5755564bdc6f74432ff."
            ),
        },
        {
            "title": "CRG-001 complete regression suite",
            "result": "540 passed",
            "detail": (
                "Final-state repository regression completed "
                "with 37 known deprecation warnings, "
                "0 failures and 0 collection errors."
            ),
        },
        {
            "title": "CRG-001 focused closure suite",
            "result": "12 passed",
            "detail": (
                "Programme Progress and canonical assessment "
                "closure contracts passed."
            ),
        },
        {
            "title": "CRG-001 capability assessment",
            "result": "20 capabilities assessed",
            "detail": (
                "All P0 and P1 capabilities were reassessed "
                "against repository, database, automated-test, "
                "HTTPS and operational evidence."
            ),
        },
        {
            "title": "CRG-001 pilot readiness verdict",
            "result": "NOT READY",
            "detail": (
                "Four unresolved P0 blockers and ten total "
                "commercial blockers were confirmed."
            ),
        },
        {
            "title": "CRG-001 critical readiness gaps",
            "result": "7 critical",
            "detail": (
                "Critical gaps affect authorization, workspace "
                "isolation, audit, recovery, product access, "
                "production connectors and operations."
            ),
        },
        {
            "title": "CRG-001 canonical assessment",
            "result": "Validated",
            "detail": (
                "The assessment contains 20 readiness rows, "
                "10 blocker records and a ten-stage "
                "remediation sequence."
            ),
        },
        {
            "title": "Current full regression suite",
            "result": "536 passed",
            "detail": (
                "PRG-001 complete regression validation "
                "with 37 known deprecation warnings."
            ),
        },
        {
            "title": "SBA-007B closure baseline",
            "result": "528 passed",
            "detail": (
                "Historical full-suite baseline before "
                "PRG-001 implementation."
            ),
        },
        {
            "title": "SBA-007B focused suite",
            "result": "13 passed",
            "detail": (
                "Production preflight and operational "
                "documentation controls."
            ),
        },
        {
            "title": "Production preflight",
            "result": "0 failures, 0 warnings",
            "detail": (
                "Controlled staging-equivalent process validation."
            ),
        },
        {
            "title": "PRG-001 live HTTPS validation",
            "result": "Passed",
            "detail": (
                "Authentication, all five dashboards, "
                "cross-dashboard navigation, security "
                "headers, masking and logout verified."
            ),
        },
        {
            "title": "Validation cleanup",
            "result": "Complete",
            "detail": (
                "Temporary user, role, browser session "
                "and security-log records were removed. "
                "The runtime stopped and logs were sanitised."
            ),
        },
        {
            "title": "Strict database fail-fast",
            "result": "Passed",
            "detail": (
                "Unreachable staging database prevented "
                "application startup."
            ),
        },
        {
            "title": "SBA-007B repository publication",
            "result": "Synchronized",
            "detail": (
                "Local and remote cgms-v2-roadmap matched "
                "at c0f208d."
            ),
        },
        {
            "title": "PRG-001 repository publication",
            "result": "Synchronized",
            "detail": (
                "Local, tracked remote and direct remote "
                "cgms-v2-roadmap references matched at "
                "bcefd77198eceafd086e4e63d150037c061ce0d7."
            ),
        },
    ],
    "commits": [
        {
            "hash": "6b8a00d",
            "title": (
                "fix(ci): stabilize product readiness "
                "regression environment"
            ),
            "status": "Published",
        },
        {
            "hash": "4a43f40",
            "title": (
                "chore(pwi-001): finalize Step 187E "
                "governance currency"
            ),
            "status": "Published",
        },
        {
            "hash": "0140d4a",
            "title": "feat: add authenticated workspace switching",
            "status": "Published",
        },
        {
            "hash": "cc366ed",
            "title": (
                "feat(pwi-001): complete Step 187D "
                "tenant persistence"
            ),
            "status": "Published",
        },
        {
            "hash": "595de8f",
            "title": (
                "docs(governance): reconcile PWI-001 "
                "Step 187C publication state"
            ),
            "status": "Published",
        },
        {
            "hash": "4624bf8",
            "title": "docs(governance): close PWI-001 Step 187C",
            "status": "Published",
        },
        {
            "hash": "05dcb2d",
            "title": (
                "PWI-001 Step 187C — Workspace-Bound "
                "Authentication Principals"
            ),
            "status": "Published",
        },
        {
            "hash": "16a673d",
            "title": (
                "docs(governance): record CRG-001 "
                "readiness assessment"
            ),
            "status": "Published",
        },
        {
            "hash": "bcefd77",
            "title": (
                "feat(dashboard): add programme progress hub"
            ),
            "status": "Published",
        },
        {
            "hash": "c0f208d",
            "title": (
                "docs(governance): record SBA-007B closure"
            ),
            "status": "Published",
        },
        {
            "hash": "be8fa24",
            "title": (
                "feat(operations): add production "
                "deployment preflight"
            ),
            "status": "Published",
        },
        {
            "hash": "318be65",
            "title": (
                "feat(runtime): harden production startup policy"
            ),
            "status": "Published",
        },
        {
            "hash": "ec5bf09",
            "title": (
                "feat(auth): add persistent login "
                "throttling controls"
            ),
            "status": "Published",
        },
        {
            "hash": "3f8cfc4",
            "title": (
                "style(patent): polish readiness dashboard layout"
            ),
            "status": "Published",
        },
    ],
    "startup": [
        {
            "title": "1. Select the approved Python environment",
            "purpose": (
                "Use the short external Python 3.11 "
                "environment established for CGMS."
            ),
            "command": (
                '$Python = '
                '"C:\\venvs\\cgms311\\Scripts\\python.exe"'
            ),
        },
        {
            "title": "2. Start the local PostgreSQL database",
            "purpose": (
                "Launch the governed local-development "
                "database container."
            ),
            "command": "docker compose up -d db",
        },
        {
            "title": "3. Start the canonical HTTPS dashboard",
            "purpose": (
                "Required for secure browser-session cookies "
                "and protected dashboards."
            ),
            "command": (
                '& $Python -m uvicorn '
                'app.dashboard.main:app `\n'
                '    --host 127.0.0.1 `\n'
                '    --port 8443 `\n'
                '    --ssl-certfile '
                '.\\certs\\local-dev-cert.pem `\n'
                '    --ssl-keyfile '
                '.\\certs\\local-dev-key.pem'
            ),
        },
        {
            "title": "4. Open the secure sign-in page",
            "purpose": (
                "Authenticate before opening protected "
                "governance dashboards."
            ),
            "command": (
                'Start-Process '
                '"https://127.0.0.1:8443/auth/login"'
            ),
        },
        {
            "title": "5. Open the Programme Progress Dashboard",
            "purpose": (
                "Open the authoritative progress and "
                "navigation hub after authentication."
            ),
            "command": (
                'Start-Process '
                '"https://127.0.0.1:8443/progress"'
            ),
        },
        {
            "title": "Production preflight",
            "purpose": (
                "Run from the same environment that will "
                "launch a staging or production process."
            ),
            "command": (
                '& $Python '
                'scripts/operations/production_preflight.py'
            ),
        },
    ],
    "related_tools": [
        {
            "title": "Patent evidence package",
            "path": (
                "/patent-readiness/evidence-package"
            ),
            "description": (
                "Authenticated export of the governed "
                "Patent and IP evidence package."
            ),
        },
    ],
    "technical_debt": [
        {
            "title": "Duplicate route registrations",
            "detail": (
                "Fourteen duplicate API paths pre-date PRG-001. "
                "They remain outside the approved dashboard scope."
            ),
        },
        {
            "title": "Legacy main dashboard concentration",
            "detail": (
                "dashboard.html contains approximately "
                "18,165 lines and 437 KB of embedded logic."
            ),
        },
        {
            "title": "FastAPI lifecycle deprecation",
            "detail": (
                "Legacy on_event usage remains outside the "
                "current milestone."
            ),
        },
        {
            "title": "TemplateResponse deprecation warnings",
            "detail": (
                "Legacy positional TemplateResponse calls "
                "remain in older routes."
            ),
        },
        {
            "title": "Database migration framework",
            "detail": (
                "No formal migration framework currently exists. "
                "Schema changes require explicit procedures."
            ),
        },
        {
            "title": "Readiness probes",
            "detail": (
                "/system/health and /system/environment are "
                "informational, not authoritative readiness probes."
            ),
        },
    ],
    "governance": {
        "rule": "Engineering Governance Rule EG-001",
        "classification": (
            "Approved Readiness Currency Closure — "
            "CAP-004 Step 264T"
        ),
        "approval_date": "23 August 2026",
        "canonical_record": (
            "docs/CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md"
        ),
        "scope": (
            "Controlled CAP-004 readiness and governance-currency "
            "update recording the Step 264S PASS determination, "
            "PILOT_READY promotion, derived readiness recalculation "
            "and CRG-001 commercial-blocker closure."
        ),
        "boundaries": (
            "CAP-004 P0 priority retained; CAP-005 remains the unresolved "
            "P0 commercial blocker; pilot verdict remains NOT READY; "
            "no database access, staging, commit, push, publication or "
            "unrelated repository mutation."
        ),
    },
}


class ProgrammeProgressRegistry:
    """
    Build an isolated copy of the governed programme-progress view.

    The registry deliberately returns a deep copy so route or template
    consumers cannot mutate the canonical process-level dataset.
    """

    def build_view(self) -> dict[str, Any]:
        return deepcopy(_PROGRAMME_PROGRESS)
