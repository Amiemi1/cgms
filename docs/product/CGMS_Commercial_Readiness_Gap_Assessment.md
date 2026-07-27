# CGMS Commercial Readiness Gap Assessment

**Milestone:** CRG-001
**Programme sprint:** Sprint 20
**Classification:** Planned Work under Engineering Governance Rule EG-001
**Assessment date:** 27 July 2026
**Branch:** `cgms-v2-roadmap`
**Assessment status:** Complete, regression-validated, committed and published
**Pilot readiness verdict:** **NOT READY**
**Published assessment commit:** `16a673d80091d72f011ce5755564bdc6f74432ff`
**Canonical governance record:** `docs/CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md`

---

## 1. Purpose

This assessment establishes the evidence-based commercial readiness position of the Contextual Group Memory System before any controlled customer or enterprise pilot.

It reassesses every P0 and P1 capability in the approved Product Capability and Feature Prioritization Matrix against:

- repository implementation evidence;
- database models and live schema;
- automated tests;
- browser authentication and authorization behaviour;
- live HTTPS access behaviour;
- persistence across database sessions and operating-system processes;
- connector and operational controls;
- backup and recovery capability;
- product-interface and navigation implementation;
- Engineering Governance Rule EG-001.

This document is an assessment and sequencing record. It does not authorize remediation, migration, connector activation, product redesign or pilot deployment.

---

## 2. Executive Decision

Twenty P0 and P1 capabilities were assessed.

| Measure | Result |
|---|---:|
| Capabilities assessed | 20 |
| Validated | 1 |
| Partial | 15 |
| Not Ready | 3 |
| Not Implemented | 1 |
| Critical-severity capabilities | 7 |
| High-severity capabilities | 12 |
| Low-severity capabilities | 1 |
| P0 commercial blockers | 4 |
| Total commercial blockers | 10 |

The provisional commercial pilot verdict is **NOT READY**.

The principal reasons are:

1. production authentication exists, but authorization is not enforced consistently across the application;
2. persistent and enforceable workspace isolation is absent;
3. the enterprise audit trail is incomplete;
4. governed backup, restore and recovery controls are absent;
5. no production connector has been validated;
6. the Knowledge Worker Interface and Operator Console expose anonymous access paths;
7. user-facing memory, intelligence and operational records are not bound to a persistent workspace identity.

---

## 3. Assessment Method

The assessment used the following evidence classes.

### 3.1 Static implementation inspection

Python source, dashboard routes, templates, services, models, documentation and tests were inspected for:

- persistence;
- authentication and authorization dependencies;
- workspace identity and tenant scope;
- lifecycle behaviour;
- connector controls;
- audit behaviour;
- backup and recovery procedures;
- product navigation;
- user and browser identity binding.

### 3.2 Automated validation

Focused regression suites were executed for authentication, authorization, audit, memory, intelligence, product experience, connectors and operations.

Exact test totals are recorded only where they were captured directly in the validation output. No unsupported totals are inferred.

### 3.3 Database validation

The live PostgreSQL database was inspected for:

- persistent models and tables;
- workspace fields;
- security-log records;
- memory, goal, decision, score and connector records;
- persistence across independent sessions;
- persistence across a separate Python process.

### 3.4 Live HTTPS validation

Anonymous and authenticated access behaviour was evaluated against principal product routes.

### 3.5 Operational validation

PostgreSQL backup tools were exercised through a temporary, non-restored logical dump. The archive was parsed and deleted immediately.

### 3.6 Repository integrity

Every assessment stage ended with:

- a clean working tree;
- synchronized `cgms-v2-roadmap` branch state;
- no modification to `manual_test_db.py`;
- continued HTTPS runtime availability.

---

## 4. Readiness Status Definitions

| Status | Meaning |
|---|---|
| Validated | The capability is implemented and supported by sufficient automated, persistent and live evidence for its assessed boundary. |
| Partial | Material implementation exists, but one or more commercial, security, persistence, workspace, quality or operational controls remain incomplete. |
| Not Ready | Technical foundations may exist, but the capability cannot currently support a governed commercial pilot. |
| Not Implemented | No executable product implementation or persistent product state was established. |

A capability may be technically functional while remaining commercially blocked.

---

## 5. Consolidated P0/P1 Readiness Register

| ID | Capability | Priority | Domain | Documented Status | CRG-001 Status | Severity | Commercial Blocker |
|---|---|---|---|---|---|---|---|
| CAP-001 | Secure Authentication | P0 | Governance | Partial | Validated | Low | No |
| CAP-002 | Role-Based Access Control | P0 | Governance | Partial | Partial | Critical | Yes |
| CAP-003 | Workspace Isolation | P0 | Governance / Memory | Partial | Not Ready | Critical | Yes |
| CAP-004 | Persistent Audit Store | P0 | Governance | Partial | Partial | Critical | Yes |
| CAP-005 | Backup and Restore | P0 | Operations | Planned | Not Ready | Critical | Yes |
| CAP-006 | Structured Organizational Memory | P1 | Memory | Implemented | Partial | High | No |
| CAP-007 | Memory Lifecycle Actions | P1 | Memory | Implemented | Partial | High | No |
| CAP-008 | Enterprise Memory Intelligence | P1 | Intelligence | Implemented | Partial | High | No |
| CAP-009 | Explainability | P1 | Intelligence / Governance | Implemented | Partial | High | No |
| CAP-010 | Semantic Search | P1 | Intelligence | Partial | Partial | High | No |
| CAP-011 | Decision Memory | P1 | Memory / Intelligence | Partial | Partial | High | No |
| CAP-012 | Tasks and Goals | P1 | Memory / Operations | Implemented | Partial | High | No |
| CAP-013 | Persistent Timeline | P1 | Memory / Operations | Partial | Partial | High | No |
| CAP-014 | Executive Memory Dashboard | P1 | Intelligence | Partial | Partial | High | No |
| CAP-015 | Guided Onboarding | P1 | Product Experience | Planned | Not Implemented | High | Yes |
| CAP-016 | Knowledge Worker Interface | P1 | Product Experience | Partial | Partial | Critical | Yes |
| CAP-017 | Product Navigation Shell | P1 | Product Experience | Planned | Partial | High | Yes |
| CAP-018 | Connector Health | P1 | Operations | Implemented | Partial | High | Yes |
| CAP-019 | First Production Connector | P1 | Integrations | Partial | Not Ready | Critical | Yes |
| CAP-021 | Operator Console | P1 | Operations | Implemented | Partial | Critical | Yes |

---

## 6. Capability Findings

### CAP-001 — Secure Authentication

**Assessment:** Validated

Authentication, secure browser sessions, Cross-Site Request Forgery protection, login throttling, credential verification, logout behaviour and session registration were validated.

Focused authentication and authorization validation recorded **279 passed** with known non-blocking deprecation warnings.

No material CAP-001 capability gap was established during CRG-001.

### CAP-002 — Role-Based Access Control

**Assessment:** Partial
**Commercial blocker:** Yes

The canonical roles, permission policy, account-role revalidation and authorization dependency are implemented and validated.

Application-wide enforcement is incomplete. Anonymous HTTP `200` responses were confirmed for product and operational surfaces that should be permission-controlled.

Affected boundaries include:

- `/dashboard`;
- `/operator`;
- `/operator/console`;
- `/product-readiness/dashboard`;
- connector routes;
- ingestion routes;
- workspace administration routes;
- memory and intelligence routes.

The authorization engine is valid, but route coverage is incomplete.

### CAP-003 — Workspace Isolation

**Assessment:** Not Ready
**Commercial blocker:** Yes

The repository contains workspace-labelled services and routes, but no persistent enterprise workspace boundary was established.

The assessment found:

- no persistent Workspace model;
- no persistent workspace-membership model;
- no `workspace_id` field on Memory or Goal;
- no workspace field on decision, score, relationship or connector records;
- process-local workspace administration and quota state;
- no cross-workspace denial tests;
- no consistent workspace authorization dependency.

The current implementation is an operational prototype, not enforceable tenant isolation.

### CAP-004 — Persistent Audit Store

**Assessment:** Partial
**Commercial blocker:** Yes

The database-backed security audit subsystem is validated.

Evidence included:

- four persistent `SecurityLog` records;
- identical records across independent database sessions;
- identical record identifiers in a separate Python process;
- persisted login success and failure records;
- transactional browser-session revocation auditing;
- authorized security-audit reading;
- **68 focused tests passed**.

The general Event Bus audit subscriber still uses an in-memory list. The explainability audit store also remains in-memory.

CGMS therefore lacks one persistent enterprise audit trail covering security, domain events, explanations and governance activity.

### CAP-005 — Backup and Restore

**Assessment:** Not Ready
**Commercial blocker:** Yes

PostgreSQL backup tooling is available.

A temporary custom-format logical dump was created successfully:

- archive size: **40,984 bytes**;
- parseable archive entries: **126**;
- temporary dump cleanup: passed;
- production database volume: `cgms_cgms_data`;
- restore operation: not attempted.

CGMS lacks:

- governed backup scripts;
- retention controls;
- backup encryption;
- checksum or integrity verification procedures;
- automated restore testing;
- recovery runbooks;
- recovery point objective;
- recovery time objective.

Tool availability does not constitute an implemented recovery capability.

### CAP-006 — Structured Organizational Memory

**Assessment:** Partial

A persistent and structured Memory model exists with summary, type, status, priority, importance, reminders, relationships and decision-integrity fields.

The capability lacks:

- workspace identity;
- consistent authenticated route access;
- live pilot memory evidence in the assessed database.

### CAP-007 — Memory Lifecycle Actions

**Assessment:** Partial

Complete, soft-delete, restore, reopen, delay and parent-chain lifecycle operations exist.

The lifecycle routes are not consistently protected, and dedicated lifecycle regression tests were not established during the assessment.

### CAP-008 — Enterprise Memory Intelligence

**Assessment:** Partial

Persistent `MemoryScore` storage, scoring factors, cache behaviour and event-subscriber logic exist. Focused Memory Intelligence tests were located and executed successfully.

The capability remains incomplete because:

- score-cache routes lack authorization;
- intelligence records are not workspace-scoped;
- process-local cache state remains part of the runtime boundary.

### CAP-009 — Explainability

**Assessment:** Partial

Explanation, factor-generation, reasoning and tracing services exist.

However:

- no dedicated explainability test suite was established;
- explanation evidence is not stored through a durable explanation model;
- the explainability audit store is process-local;
- routes are not consistently authorized or workspace-scoped.

### CAP-010 — Semantic Search

**Assessment:** Partial

The implementation includes:

- a PostgreSQL vector column;
- sentence-transformer dependencies;
- pgvector support;
- embedding services;
- vector-search services;
- database-backed retrieval logic.

The assessment did not initialize or download an embedding model.

Commercial readiness was not established because there is no verified:

- embedding-runtime execution;
- relevance-quality suite;
- workspace-scoped retrieval;
- authorized search boundary;
- explainable search-result contract.

### CAP-011 — Decision Memory

**Assessment:** Partial

A persistent `DecisionLineage` model, decision hashes, verification fields, trace services and decision reasoning services exist.

No decision-specific tests, live decision records or workspace scope were established.

### CAP-012 — Tasks and Goals

**Assessment:** Partial

Persistent Goal records, task dependencies, priorities, progress calculation, automatic completion and reflection services exist.

The capability lacks:

- dedicated task and goal workflow tests;
- consistent route authorization;
- workspace identity;
- live pilot records in the assessed database.

### CAP-013 — Persistent Timeline

**Assessment:** Partial

Timeline services reconstruct chronological views from persistent memories and relationships.

No dedicated institutional timeline or event-history model, timeline-specific tests or workspace scope was established.

A reconstructed view is not automatically a persistent enterprise timeline.

### CAP-014 — Executive Memory Dashboard

**Assessment:** Partial

The existing `/dashboard` is a substantial executive-memory and intelligence baseline.

It contains:

- Memory;
- Insights;
- Next Best Action;
- Decision Feed;
- Runtime Event Audit Trail;
- Priority Tasks;
- Runtime Reliability;
- cross-dashboard navigation.

The template contains approximately **420,657 bytes** and **18,235 lines**.

Commercial gaps include:

- anonymous access;
- no browser-identity binding;
- no workspace context;
- no workspace switcher;
- browser-local operational analytics;
- no validated executive-metric contract;
- excessive concentration of product concerns in one composite interface.

### CAP-015 — Guided Onboarding

**Assessment:** Not Implemented
**Commercial blocker:** Yes

No onboarding route, interface, persisted onboarding state or onboarding test exists.

The capability currently appears only in planning and Product Readiness documentation.

### CAP-016 — Knowledge Worker Interface

**Assessment:** Partial
**Commercial blocker:** Yes

The existing `/dashboard` contains the principal knowledge-worker modules:

- memory;
- tasks;
- goals;
- decisions;
- insights;
- timeline;
- search;
- prioritization;
- next actions.

However:

- anonymous users can open the interface;
- no authenticated browser identity is bound to the interface;
- no workspace context is present;
- API requests use a hard-coded negative user identifier.

The interface is functionally substantial but commercially unsafe.

### CAP-017 — Product Navigation Shell

**Assessment:** Partial
**Commercial blocker:** Yes

Static cross-dashboard navigation exists among the principal product interfaces.

The approved Product Navigation Shell is not complete because there is no:

- shared base template or navigation component;
- active-page indication;
- consistent role-aware navigation;
- workspace switcher;
- centralized browser identity;
- centralized workspace context;
- material navigation-specific test coverage.

### CAP-018 — Connector Health

**Assessment:** Partial
**Commercial blocker:** Yes

Connector registry, activation and health functions exist, with focused automated tests.

Connector health is not persisted. There is no connector-health table, durable last-success or last-failure history, or consistent authorization boundary.

### CAP-019 — First Production Connector

**Assessment:** Not Ready
**Commercial blocker:** Yes

Slack, Microsoft Teams, Gmail and Calendar adapter prototypes exist. Adapter and ingestion tests were executed successfully.

No adapter currently demonstrates the full production control set:

- governed credentials;
- externalized durable configuration;
- persistent connector records;
- persistent workspace binding;
- retries and backoff;
- idempotency and deduplication;
- persistent failure audit;
- controlled external pilot evidence.

### CAP-021 — Operator Console

**Assessment:** Partial
**Commercial blocker:** Yes

The Operator Console provides:

- runtime health;
- workspace count;
- connector status;
- runtime timeline;
- event count;
- error count;
- operator actions.

Anonymous HTTP `200` access was confirmed for both the HTML console and operational JSON.

The interface lacks browser-identity binding and workspace selection. Operational actions and state require an authenticated permission boundary.

---

## 7. Critical Gap Register

| ID | Capability | Priority | Critical Gap |
|---|---|---|---|
| CAP-002 | Role-Based Access Control | P0 | Authorization is not enforced consistently across product, connector, ingestion, workspace and operational routes. |
| CAP-003 | Workspace Isolation | P0 | No persistent Workspace or membership foundation, tenant-scoped records or cross-workspace denial contract exists. |
| CAP-004 | Persistent Audit Store | P0 | Security logs persist, but Event Bus and explainability audit evidence remain process-local. |
| CAP-005 | Backup and Restore | P0 | No governed backup, retention, restore validation, recovery procedure, recovery point objective or recovery time objective exists. |
| CAP-016 | Knowledge Worker Interface | P1 | The interface is anonymously accessible, lacks identity and workspace binding, and uses a hard-coded user identifier. |
| CAP-019 | First Production Connector | P1 | No connector has the full credential, persistence, workspace, retry, idempotency, audit and pilot-validation control set. |
| CAP-021 | Operator Console | P1 | Operational HTML, JSON and action surfaces lack a consistent authenticated permission boundary. |

---

## 8. Anonymous Live-Access Evidence

| Route | Anonymous Result | Assessment |
|---|---:|---|
| `/dashboard` | HTTP 200 | Unprotected |
| `/progress` | HTTP 401 | Protected |
| `/operator` | HTTP 200 | Unprotected |
| `/operator/console` | HTTP 200 | Unprotected |
| `/product-readiness/dashboard` | HTTP 200 | Unprotected |
| `/patent-readiness/dashboard` | HTTP 401 | Protected |

The mixed results demonstrate that authentication and authorization controls exist but are not applied consistently.

---

## 9. Pilot Entry Criteria

The pilot verdict may not be upgraded until all of the following minimum conditions are satisfied:

1. all commercially sensitive HTML, JSON and mutation routes enforce authenticated permissions;
2. persistent Workspace and membership models exist;
3. customer records are tenant-scoped and cross-workspace access is denied by tests;
4. security, domain-event and explainability evidence is persisted through a unified audit boundary;
5. backup creation, retention, encryption, verification and restore testing are implemented;
6. the Knowledge Worker and Operator interfaces bind the authenticated user and active workspace;
7. at least one connector satisfies the production connector control standard;
8. core memory, decision, timeline and task workflows have dedicated regression coverage;
9. semantic-search relevance and isolation are validated;
10. a controlled pilot validation is separately approved under EG-001.

---

## 10. Proposed Remediation Sequence

The sequence below is a planning recommendation only.

| Sequence | Proposed Milestone | Capabilities | Proposed Classification |
|---:|---|---|---|
| 1 | Application-Wide Authorization Enforcement | CAP-002, CAP-016, CAP-018, CAP-019, CAP-021 | Mandatory security intervention |
| 2 | Persistent Workspace Isolation Foundation | CAP-003 and all workspace-dependent capabilities | Mandatory architectural intervention |
| 3 | Unified Persistent Enterprise Audit | CAP-004 | Planned remediation milestone |
| 4 | Backup, Restore and Recovery Controls | CAP-005 | Planned operational-readiness milestone |
| 5 | Identity-Bound Product Shell and Workspace Experience | CAP-014, CAP-016, CAP-017 | Planned product-experience milestone |
| 6 | Production Connector Foundation and Pilot Adapter | CAP-018, CAP-019 | Planned integration milestone |
| 7 | Core Memory and Decision Workflow Hardening | CAP-006, CAP-007, CAP-011, CAP-012, CAP-013 | Planned capability-hardening milestone |
| 8 | Intelligence, Explainability and Search Validation | CAP-008, CAP-009, CAP-010, CAP-014 | Planned intelligence-quality milestone |
| 9 | Guided Onboarding | CAP-015 | Planned product-adoption milestone |
| 10 | Controlled Commercial Pilot Validation | All P0 and P1 capabilities | Pilot authorization milestone |

---

## 11. Sequencing Dependencies

The remediation sequence is dependency-driven.

- Application-wide authorization must precede exposure of customer, connector and operational interfaces.
- Workspace isolation must precede tenant-scoped memory, intelligence, connector and audit claims.
- Audit persistence and recovery controls must precede enterprise pilot authorization.
- The product shell must consume authenticated identity and persistent workspace context.
- A pilot connector must depend on persistent connector configuration, workspace scope and operational health.
- Intelligence-quality validation must use workspace-scoped production-like data.
- Guided Onboarding should target the hardened product shell and production connector workflow rather than the current prototype surfaces.

No later P1 enhancement should displace unresolved P0 security, isolation, audit or recovery controls without explicit EG-001 approval.

---

## 12. Evidence Summary

High-value evidence established during CRG-001 includes:

- authentication and RBAC mechanism validation: **279 passed**;
- persistent-audit focused validation: **68 passed**;
- historical PRG-001 full-suite baseline before CRG-001 closure work: **536 passed** with **37 known deprecation warnings**;
- focused CRG-001 closure validation: **12 passed**;
- complete final-state regression validation: **540 passed** with **37 known deprecation warnings**;
- persistent security-log records verified across sessions and processes;
- PostgreSQL logical dump successfully parsed with **126 archive entries**;
- no persistent Workspace model or workspace field on principal customer records;
- no connector or connector-health database table;
- no onboarding state table;
- zero Memory, Goal, DecisionLineage and MemoryScore records in the assessed database;
- protected access for Programme Progress and Patent Readiness;
- anonymous access for the Knowledge Worker Interface, Operator Console and Product Readiness dashboard;
- clean repository after every assessment stage;
- `manual_test_db.py` unchanged.

---

## 13. Governance Boundary

CRG-001 remains an assessment and governance-closure milestone.

This document does not authorize:

- route hardening;
- database or schema migrations;
- workspace-model implementation;
- audit-store implementation;
- backup or restore implementation;
- connector configuration or activation;
- Product Navigation Shell implementation;
- Knowledge Worker Interface redesign;
- Operator Console redesign;
- technical-debt remediation;
- commercial pilot execution.

Each remediation milestone requires an applicable EG-001 classification and explicit approval before implementation.

---

## 14. Assessment Conclusion

CGMS has a broad and technically substantial product foundation. Secure authentication, persistent memory structures, intelligence engines, decision lineage, dashboard interfaces, connector adapters and operational tooling are demonstrably present.

The system is not yet commercially pilot-ready because its strongest implemented capabilities are not consistently enclosed by enterprise authorization, persistent tenant isolation, unified auditability and recoverability.

The immediate programme priority is therefore not additional feature breadth. It is the governed conversion of the existing platform into a secure, isolated, auditable and recoverable enterprise product.

**CRG-001 pilot readiness verdict: NOT READY.**

The assessment was committed and published as `16a673d80091d72f011ce5755564bdc6f74432ff` on `origin/cgms-v2-roadmap`.
