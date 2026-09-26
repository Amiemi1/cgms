from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\MurphyPersonal\OneDrive\Desktop"
    r"\Contextual_Group_Memory_System"
    r"\05_Prototype_and_Testing\cgms\cgms"
)

TARGET_FILE = (
    PROJECT_ROOT
    / "docs"
    / "product"
    / "CGMS_Product_Capability_and_Feature_Prioritization_Matrix.md"
)

CONTENT = r"""# CGMS Product Capability and Feature Prioritization Matrix

## Enterprise Productization Milestone

**Product:** Contextual Group Memory System  
**Abbreviation:** CGMS  
**Strategic Phase:** Phase II – Enterprise Productization  
**Current Engineering Baseline:** CGMS v1.75 – Enterprise Event Bus  
**Current Product Baseline:** Minimum Lovable Product  
**Document Owner:** Product Architecture  
**Status:** Approved Prioritization Matrix  
**Document Type:** Living Product Artifact

---

# 1. Purpose

This document prioritizes CGMS capabilities according to customer value, commercial relevance, technical readiness, security dependency, pilot importance, and release sequencing.

It provides the governing basis for deciding:

- what must be completed before pilot;
- what belongs in the Minimum Lovable Product;
- what can be deferred;
- what requires security or infrastructure hardening;
- what should be customer-facing;
- what remains platform-only;
- what should be validated commercially before further investment.

---

# 2. Prioritization Principles

Capabilities are prioritized using the following criteria:

1. customer value;
2. strength of problem-solution fit;
3. importance to the flagship workflow;
4. commercial differentiation;
5. technical readiness;
6. security and compliance dependency;
7. pilot necessity;
8. implementation risk;
9. evidence required;
10. roadmap alignment.

---

# 3. Priority Levels

## P0 — Commercial Blocker

A capability without which CGMS cannot credibly enter pilot or commercial use.

## P1 — Core MLP Requirement

A capability required to deliver the approved Minimum Lovable Product promise.

## P2 — Pilot Enhancement

A capability that improves pilot value but is not required for initial controlled use.

## P3 — Post-Pilot Expansion

A capability that should follow customer validation.

## P4 — Long-Term Platform Vision

A strategically important capability outside the first commercial release.

---

# 4. Readiness Status

## Implemented

The core technical capability exists and is regression protected.

## Partially Implemented

A technical foundation exists, but customer-facing completion or hardening is required.

## Planned

Approved but not implemented.

## Future

Part of the long-term platform vision.

---

# 5. Product Capability Matrix

| ID | Capability | Product Pillar | Priority | MLP | Pilot | Technical Readiness | Security Dependency | Customer Value | Commercial Importance | Target |
|---|---|---|---|---:|---:|---|---|---|---|---|
| CAP-001 | Secure Authentication | Governance | P0 | Yes | Yes | Implemented | Critical | High | Critical | Pre-Pilot |
| CAP-002 | Role-Based Access Control | Governance | P0 | Yes | Yes | Implemented | Critical | High | Critical | Pre-Pilot |
| CAP-003 | Workspace Isolation | Governance / Memory | P0 | Yes | Yes | Implemented | Critical | High | Critical | Pre-Pilot |
| CAP-004 | Persistent Audit Store | Governance | P0 | Yes | Yes | Implemented | Critical | High | Critical | Pre-Pilot |
| CAP-005 | Backup and Restore | Operations | P0 | Yes | Yes | Implemented | High | High | Critical | Pre-Pilot |
| CAP-006 | Structured Organizational Memory | Memory | P1 | Yes | Yes | Implemented | Medium | Critical | Critical | MLP |
| CAP-007 | Memory Lifecycle Actions | Memory | P1 | Yes | Yes | Implemented | Medium | High | High | MLP |
| CAP-008 | Enterprise Memory Intelligence | Intelligence | P1 | Yes | Yes | Implemented | Medium | Critical | Critical | MLP |
| CAP-009 | Explainability | Intelligence / Governance | P1 | Yes | Yes | Implemented | Medium | Critical | Critical | MLP |
| CAP-010 | Semantic Search | Intelligence | P1 | Yes | Yes | Partial | Medium | Critical | Critical | MLP |
| CAP-011 | Decision Memory | Memory / Intelligence | P1 | Yes | Yes | Partial | Medium | Critical | Critical | MLP |
| CAP-012 | Tasks and Goals | Memory / Operations | P1 | Yes | Yes | Implemented | Medium | High | High | MLP |
| CAP-013 | Persistent Timeline | Memory / Operations | P1 | Yes | Yes | Partial | Medium | High | High | MLP |
| CAP-014 | Executive Memory Dashboard | Intelligence | P1 | Yes | Yes | Partial | Medium | High | Critical | MLP |
| CAP-015 | Guided Onboarding | Product Experience | P1 | Yes | Yes | Planned | Medium | High | Critical | MLP |
| CAP-016 | Knowledge Worker Interface | Product Experience | P1 | Yes | Yes | Partial | Medium | Critical | Critical | MLP |
| CAP-017 | Product Navigation Shell | Product Experience | P1 | Yes | Yes | Planned | Low | Critical | Critical | MLP |
| CAP-018 | Connector Health | Operations | P1 | Yes | Yes | Implemented | High | High | High | MLP |
| CAP-019 | First Production Connector | Integrations | P1 | Yes | Yes | Partial | High | Critical | Critical | Pilot |
| CAP-020 | Second Production Connector | Integrations | P2 | Preferred | Yes | Partial | High | High | High | Pilot |
| CAP-021 | Operator Console | Operations | P1 | Yes | Yes | Implemented | High | Medium | High | MLP |
| CAP-022 | Runtime Controls | Operations | P2 | Limited | Limited | Implemented | Critical | Medium | Medium | Pilot |
| CAP-023 | Workspace Metrics | Operations | P2 | Yes | Yes | Implemented | Medium | Medium | Medium | Pilot |
| CAP-024 | Memory Relationship View | Intelligence | P2 | Preferred | Yes | Partial | Medium | High | High | Pilot |
| CAP-025 | Decision Lineage | Governance / Intelligence | P2 | Preferred | Yes | Partial | Medium | High | High | Pilot |
| CAP-026 | Notifications | Operations | P2 | No | Preferred | Planned | Medium | Medium | Medium | Pilot |
| CAP-027 | Persistent Event Observability | Operations | P2 | Limited | Yes | Partial | Medium | Medium | High | Pilot |
| CAP-028 | Enterprise Knowledge Graph | Intelligence | P3 | No | No | Foundation | High | Critical | High | Post-Pilot |
| CAP-029 | Recommendation Engine | Intelligence | P3 | No | No | Planned | High | High | High | Post-Pilot |
| CAP-030 | Documentation Intelligence | Knowledge Platform | P3 | No | No | Foundation | Medium | Medium | Medium | Post-Pilot |
| CAP-031 | Workflow Designer | Operations | P3 | No | No | Future | High | Medium | Medium | Post-Pilot |
| CAP-032 | Advanced Analytics | Intelligence | P3 | No | No | Partial | Medium | Medium | Medium | Post-Pilot |
| CAP-033 | Commercial Billing Automation | Commercial | P3 | No | No | Partial | High | Medium | Medium | Post-Pilot |
| CAP-034 | Multi-Agent Orchestration | Intelligence / Operations | P4 | No | No | Foundation | Critical | High | Strategic | Long-Term |
| CAP-035 | Autonomous Learning | Intelligence | P4 | No | No | Future | Critical | High | Strategic | Long-Term |
| CAP-036 | Organizational Digital Twin | Intelligence | P4 | No | No | Future | Critical | High | Strategic | Long-Term |
| CAP-037 | Distributed Event Broker | Operations | P4 | No | No | Future | High | Low Initially | Strategic | Scale Stage |
| CAP-038 | Connector Marketplace | Integrations | P4 | No | No | Future | High | Medium | Strategic | Scale Stage |

---

# 6. P0 Commercial Blockers

The following must be resolved before a real customer pilot:

1. authentication hardening;
2. role-based access control;
3. workspace isolation verification;
4. persistent audit;
5. backup and restore;
6. secrets management;
7. production deployment controls;
8. security documentation;
9. critical error handling;
10. operational recovery procedures.

No customer pilot should begin with unresolved P0 items.

---

# 7. P1 Minimum Lovable Product Scope

The MLP must include:

- structured memory;
- lifecycle actions;
- Memory Intelligence;
- explainability;
- semantic search;
- decision memory;
- tasks and goals;
- timeline;
- executive dashboard;
- guided onboarding;
- coherent navigation;
- knowledge-worker experience;
- workspace controls;
- connector health;
- at least one production-ready connector;
- operator visibility;
- audit persistence.

---

# 8. Pilot Scope Recommendation

The controlled pilot should include:

- one organization;
- one department or project team;
- 15 to 50 users;
- one production connector;
- an optional second connector;
- one flagship workflow;
- executive sponsor;
- named administrator;
- weekly product feedback;
- measurable adoption and retrieval outcomes.

---

# 9. Flagship Workflow Dependencies

The approved workflow is:

```text
Capture
  ↓
Score
  ↓
Connect
  ↓
Retrieve
  ↓
Explain
```

Required capability dependencies:

| Workflow Stage | Required Capabilities |
|---|---|
| Capture | Workspaces, Memory Creation, Connector Ingestion |
| Score | Memory Intelligence, Priority, Freshness, Confidence |
| Connect | Relationships, Decisions, Tasks, Goals, Timeline |
| Retrieve | Semantic Search, Filters, Workspace Scope |
| Explain | Explainability, Source, Audit, Relevance Reason |

---

# 10. Customer-Facing vs Platform-Only Capabilities

## Customer-Facing

- memory;
- intelligence;
- decisions;
- tasks;
- goals;
- timeline;
- search;
- workspaces;
- integrations;
- governance;
- executive dashboards.

## Platform-Only

- Enterprise Event Bus internals;
- event registry;
- subscribers;
- dispatch result;
- internal runtime wiring;
- internal service contracts;
- database implementation;
- internal orchestration.

Platform-only capabilities must support the product without becoming the primary product language.

---

# 11. Build, Harden, or Reuse Decision

## Build

Build when the capability is a CGMS differentiator:

- Memory Intelligence;
- explainability;
- institutional memory model;
- decision lineage;
- contextual timeline;
- knowledge graph;
- Documentation Intelligence.

## Harden

Harden when a foundation already exists:

- workspaces;
- connectors;
- runtime;
- operator console;
- event bus;
- audit;
- semantic search;
- dashboards.

## Reuse

Use established libraries or managed services where differentiation is low:

- authentication protocol implementation;
- secrets storage;
- monitoring infrastructure;
- database backup tooling;
- email delivery;
- object storage;
- deployment automation.

---

# 12. Security Dependency Matrix

| Capability | Security Dependency |
|---|---|
| Authentication | Critical |
| RBAC | Critical |
| Workspace Isolation | Critical |
| Connectors | High |
| Audit | High |
| Search | High |
| Memory | High |
| Timeline | High |
| Dashboard | Medium |
| Operator Controls | Critical |
| Knowledge Graph | High |
| Recommendations | High |

Security work is part of product delivery, not a later infrastructure exercise.

---

# 13. Release Sequencing

## Release A — Commercial Foundation

Focus:

- security;
- audit;
- navigation shell;
- onboarding;
- core memory;
- search;
- timeline;
- one connector.

## Release B — Pilot Intelligence

Focus:

- executive dashboard;
- relationship view;
- decision lineage;
- second connector;
- product analytics;
- pilot instrumentation.

## Release C — Post-Pilot Expansion

Focus:

- knowledge graph;
- recommendations;
- advanced analytics;
- Documentation Intelligence;
- commercial packaging.

---

# 14. Evidence Requirements

Each P0 and P1 capability must have:

- production code;
- automated tests;
- integration tests;
- security review where applicable;
- UX acceptance;
- documentation;
- deployment evidence;
- pilot evidence where applicable.

---

# 15. Prioritization Decision Rules

A new feature may enter the MLP only when:

1. it directly strengthens the flagship promise;
2. it solves a validated customer problem;
3. it does not displace a P0 item;
4. it has a clear owner;
5. it has acceptance criteria;
6. it has security implications assessed;
7. it is approved through product governance.

---

# 16. Current Strategic Assessment

CGMS has strong technical foundations but remains commercially constrained by:

- incomplete user experience;
- incomplete security hardening;
- incomplete persistent audit;
- incomplete timeline productization;
- limited production-ready connectors;
- insufficient pilot evidence;
- incomplete commercial packaging.

The correct strategy is to harden and integrate before expanding the long-term cognitive roadmap.

---

# 17. Immediate Delivery Backlog

Recommended immediate order:

1. authentication and RBAC assessment;
2. workspace isolation verification;
3. persistent audit design;
4. persistent timeline design;
5. frontend shell and navigation;
6. knowledge-worker memory experience;
7. semantic search hardening;
8. executive dashboard design;
9. first connector productionization;
10. guided onboarding;
11. pilot instrumentation;
12. pilot deployment package.

---

# 18. Acceptance Criteria

This prioritization milestone is accepted when:

1. capability priorities are documented;
2. P0 blockers are explicit;
3. MLP scope is mapped;
4. pilot scope is mapped;
5. long-term capabilities are deferred appropriately;
6. security dependencies are identified;
7. release sequencing is approved;
8. immediate backlog is established;
9. Product Architecture remains aligned;
10. UX Architecture remains aligned;
11. Navigation Architecture remains aligned;
12. `CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md` is updated at milestone closure.

---

# 19. Immediate Next Milestone

The next approved milestone is:

# CGMS Commercial Readiness Gap Assessment

It will assess the current codebase and product against:

- P0 commercial blockers;
- P1 MLP requirements;
- current implementation evidence;
- missing tests;
- security gaps;
- UX gaps;
- deployment gaps;
- connector gaps;
- pilot-readiness gaps.

---

# 20. Prioritization Decision

CGMS will prioritize commercial credibility over broad feature expansion.

No P3 or P4 capability should displace unresolved P0 commercial blockers or P1 MLP requirements without explicit approval under EG-001.

---

# 21. CAP-003 Readiness Currency Update

**Update date:** 18 August 2026

**Decision:** Step 264M read-only readiness reassessment

**Currency action:** Step 264N controlled Product Readiness update

The CAP-003 technical-readiness row is updated from **Partial** to **Implemented**. The authoritative Product Readiness catalogue advances CAP-003 to **PILOT_READY** within the assessed Workspace Isolation boundary.

The promotion is supported by:

- persistent Workspace, membership and workspace-control models;
- PostgreSQL-enforced ownership across all 11 tenant-scoped tables;
- authenticated browser and Bearer workspace resolution;
- cross-workspace record, raw-SQL and route denial contracts;
- persistent lifecycle and quota authority;
- workspace-scoped connector ingestion and metrics access;
- ordered and idempotent PostgreSQL 16 / pgvector migrations;
- a complete isolated PostgreSQL regression with 685 passed tests.

CAP-003 does not claim durable connector-health history, persistent connector configuration and credentials, production connector completion or durable workspace-metrics history. Those remain governed by CAP-018, CAP-019 and CAP-023.

The Product Readiness gate retains four catalogue-level P0 gaps. The CRG-001 commercial-readiness position retains two unresolved P0 blockers, CAP-004 and CAP-005, and eight total commercial blockers.

The commercial pilot verdict remains **NOT READY**.
---

# 22. CAP-004 Readiness Currency Update

**Update date:** 25 August 2026

**Decision:** Step 264S read-only CAP-004 readiness reassessment — PASS for promotion eligibility

**Currency action:** Step 264T controlled Product Readiness and governance-currency update

The CAP-004 technical-readiness row is updated from **Partial** to **Implemented**. The authoritative Product Readiness catalogue advances CAP-004 to **PILOT_READY** while retaining its **P0** priority.

Step 264U subsequently published the validated CAP-004 closure at `f1be3064604f4b4172561bd405710f0b491a0d25`; CAP-004 remains **P0**, its commercial blocker remains closed, and CAP-005 remains the unresolved P0 commercial blocker.

The promotion is supported by:

- one unified persistent audit schema spanning security, domain events, explainability and governance;
- deterministic legacy-security backfill and origin idempotence;
- database-enforced append-only controls;
- workspace-scoped reads and cross-workspace denial;
- explicit privileged global reads;
- persistent Event Bus and explainability convergence;
- transactional producer convergence;
- ordered and idempotent PostgreSQL 16 / pgvector migration validation;
- a complete isolated regression with **696 passed** tests and no failures.

The authoritative Product Readiness recalculation after CAP-004 promotion is:

- overall Product Readiness: **27%**;
- pilot-scope readiness: **35%**;
- catalogue-level P0 gaps: **3**;
- pilot-scope gaps: **23**;
- open Product Readiness recommendations: **27**.

The CRG-001 commercial-readiness position now retains **one unresolved P0 blocker, CAP-005**, and **seven total commercial blockers**.

CAP-004 remains P0 because persistent enterprise audit continues to be mandatory for pilot and production governance.

The commercial pilot verdict remains **NOT READY**.

---

# 23. CAP-005 Readiness Currency Update

**Update date:** 23 September 2026

CAP-005 is **Implemented / PILOT_READY**, with **P0** priority retained.

Published authority: `9c683d277f46eb2c6012759c3ff45e0221e84763`.

Current metrics are **30% Product Readiness**, **39% pilot-scope readiness**, **2 catalogue P0 gaps**, **22 pilot-scope gaps**, **26 recommendations**, and **3 pilot-ready capabilities**.

CRG-001 now has **zero unresolved P0 commercial blockers** and **six total unresolved commercial blockers**.

The commercial pilot verdict remains **NOT READY**.

---

# 24. CAP-001 / CAP-002 Readiness Currency Update

**Update date:** 25 September 2026

**Decision:** bounded read-only readiness reassessment and promotion-impact projection — PASS

**Currency action:** controlled Product Readiness reconciliation authorised

CAP-001 Secure Authentication and CAP-002 Role-Based Access Control retain **P0** priority and advance from stale **Partial / IN_PROGRESS** catalogue currency to **Implemented / PILOT_READY**.

The promotion does not introduce new authentication or RBAC engineering. It reconciles the Product Readiness catalogue with evidence already established by CRG-001, AAE-001 and the current bounded reassessment.

### 24.1 CAP-001 evidence

CAP-001 was already assessed as **Validated** by CRG-001. Authentication, secure browser sessions, CSRF protection, login throttling, credential verification, logout behaviour and session registration were validated, with no material CAP-001 capability gap established.

The 25 September 2026 bounded inventory additionally confirmed:

- **6/6** targeted authentication controls present;
- the governed authentication source surface present;
- all **6/6** selected focused security test groups present;
- Product Readiness CI run **#48** successful on the current published authority.

### 24.2 CAP-002 evidence

AAE-001 closed the application-wide authorisation gap and validated CAP-002 within the existing CGMS role and permission model.

The established evidence includes:

- **106** registered APIRoutes guarded;
- **0** unguarded APIRoutes;
- **102** protected method/path registrations;
- browser, Bearer and dual-transport enforcement;
- authenticated CSRF handling for unsafe browser requests;
- controlled live HTTPS validation;
- a **570 passed** closure regression.

The 25 September 2026 bounded inventory additionally confirmed **4/4** targeted RBAC controls and all **6/6** selected focused security test groups.

### 24.3 Recalculated Product Readiness position

The controlled promotion changes current Product Readiness currency to:

- overall Product Readiness: **34%**;
- pilot-scope readiness: **46%**;
- catalogue-level P0 gaps: **0**;
- pilot-scope gaps: **20**;
- open Product Readiness recommendations: **24**;
- pilot-ready capabilities: **5**;
- in-progress capabilities: **15**.

Overall CGMS completion under the existing governed completion-weight model becomes **51%**.

The CRG-001 commercial-blocker register is unchanged by this currency reconciliation: unresolved P0 commercial blockers remain **0**, while total unresolved commercial blockers remain **6**.

The commercial pilot verdict remains **NOT READY**. Twenty pilot-required capabilities remain below pilot-ready status, other P1/commercial gaps remain open, and no production-ready capability is claimed.

This currency update does not authorise a commercial pilot, deployment, production-database action or unrelated feature expansion."""


def main() -> None:
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_FILE.write_text(CONTENT.strip() + "\n", encoding="utf-8")

    print("CGMS Product Capability and Feature Prioritization Matrix created.")
    print(f"Path: {TARGET_FILE}")
    print(f"Characters written: {len(CONTENT):,}")


if __name__ == "__main__":
    main()
