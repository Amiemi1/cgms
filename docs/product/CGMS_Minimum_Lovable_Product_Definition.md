# CGMS Minimum Lovable Product Definition

## Productization Milestone

**Product:** Contextual Group Memory System  
**Abbreviation:** CGMS  
**Strategic Phase:** Phase II – Enterprise Productization  
**Current Engineering Baseline:** CGMS v1.75 – Enterprise Event Bus  
**Document Owner:** Product Architecture  
**Status:** Approved MLP Definition  
**Document Type:** Living Product Artifact

---

# 1. Purpose

This document defines the Minimum Lovable Product for CGMS.

The MLP is the smallest commercially credible version of CGMS that:

- solves one important customer problem clearly;
- produces measurable customer value;
- is stable enough for a controlled pilot;
- demonstrates the differentiation of CGMS;
- provides a foundation for paid adoption;
- avoids unnecessary expansion into the full long-term platform vision.

The MLP is not a reduced technical prototype.

It is the first version of CGMS that a real organization can understand, use, trust, and recommend.

---

# 2. First Target Customer

The recommended first target customer is:

## Knowledge-Intensive Mid-Sized Organization

Typical profile:

- 100 to 2,000 employees;
- multiple teams or departments;
- high dependence on institutional knowledge;
- significant use of email, documents, chat, and meetings;
- recurring loss of context during staff transitions;
- weak decision traceability;
- no mature knowledge-management platform;
- willingness to participate in a controlled pilot.

Priority sectors:

1. professional services;
2. universities and research institutions;
3. non-governmental organizations;
4. engineering and software organizations;
5. public institutions with knowledge-continuity needs.

The recommended first pilot should avoid highly regulated production environments until security, compliance, and operational controls are fully hardened.

---

# 3. First Commercial Problem

The first commercial problem CGMS will solve is:

> Organizations lose critical knowledge and cannot easily recover the context behind important decisions, actions, and events.

This problem appears through:

- repeated work;
- slow onboarding;
- loss of expertise when staff leave;
- unclear decision rationale;
- fragmented information;
- weak continuity across projects;
- difficulty locating relevant context;
- inability to identify important or stale knowledge;
- poor connection between decisions, tasks, goals, and outcomes.

---

# 4. MLP Product Promise

The CGMS MLP promise is:

> CGMS helps teams preserve critical organizational knowledge and quickly recover the context behind important decisions, tasks, goals, events, and insights.

The MLP must prove that users can:

1. capture important knowledge;
2. organize it into meaningful memory types;
3. understand why it matters;
4. retrieve it later;
5. trace it to related decisions and actions;
6. identify stale or high-priority knowledge;
7. preserve continuity across people and time.

---

# 5. Flagship Workflow

The flagship workflow is:

## Capture → Score → Connect → Retrieve → Explain

```text
Organizational Input
        ↓
Memory Capture
        ↓
Memory Classification
        ↓
Memory Intelligence Scoring
        ↓
Contextual Relationships
        ↓
Semantic Retrieval
        ↓
Explainable Result
```

The workflow should feel complete to the user without requiring knowledge of the underlying architecture.

---

# 6. Primary MLP User Journey

## Step 1: Capture

A user or connector submits information such as:

- a decision;
- a task;
- a goal;
- an event;
- an insight;
- a project update;
- a risk;
- a lesson learned.

## Step 2: Classify

CGMS stores the item as a structured memory with:

- memory type;
- title;
- content;
- status;
- priority;
- owner;
- workspace;
- timestamps;
- optional relationships.

## Step 3: Score

CGMS calculates:

- importance;
- confidence;
- freshness;
- priority;
- composite memory score.

## Step 4: Explain

The user can see why the memory received its score.

## Step 5: Connect

The memory is linked to relevant:

- decisions;
- tasks;
- goals;
- events;
- insights;
- people;
- workspaces.

## Step 6: Retrieve

The user can search using natural language and retrieve relevant memories.

## Step 7: Act

The user can:

- reopen;
- complete;
- delay;
- restore;
- reprioritize;
- review related context.

---

# 7. MLP Core Capabilities

The MLP must include the following customer-facing capabilities.

## 7.1 Secure Workspaces

Users can:

- create or access a workspace;
- separate organizational contexts;
- manage basic workspace settings;
- view workspace metrics.

## 7.2 Structured Organizational Memory

Supported memory types:

- tasks;
- goals;
- events;
- decisions;
- insights;
- general memories.

Required lifecycle actions:

- create;
- update;
- complete;
- reopen;
- delay;
- restore;
- reprioritize.

## 7.3 Enterprise Memory Intelligence

Required scoring dimensions:

- importance;
- confidence;
- freshness;
- priority;
- composite.

Required outputs:

- current score;
- explanation;
- memory type;
- status;
- explicit priority.

## 7.4 Contextual Search

Users must be able to:

- search memories;
- retrieve relevant results;
- filter by memory type;
- filter by status;
- filter by workspace;
- inspect why a result is relevant.

## 7.5 Decision Context

Users must be able to:

- store a decision;
- record rationale;
- associate supporting context;
- connect actions and outcomes;
- retrieve the decision later.

## 7.6 Timeline

Users must be able to:

- see important organizational events over time;
- inspect memory changes;
- understand sequence and context.

## 7.7 Audit Foundation

The system must:

- record important domain events;
- identify source;
- identify workspace where available;
- preserve event timestamp;
- support later persistent audit expansion.

## 7.8 Connector Pilot

The MLP should include no more than two production-ready connectors.

Recommended first connectors:

1. Gmail or Microsoft Outlook;
2. Slack or Microsoft Teams.

Connector choice should depend on the first pilot customer.

## 7.9 Operator and Administration View

Administrators and operators must be able to:

- inspect system health;
- inspect connector health;
- review ingestion activity;
- manage basic quotas;
- inspect runtime events;
- manage workspaces.

## 7.10 Executive Memory Dashboard

The dashboard should show:

- total memories;
- high-priority memories;
- stale memories;
- recent decisions;
- unresolved tasks;
- memory score distribution;
- workspace activity;
- connector activity.

---

# 8. MLP Experience Requirements

The MLP must provide a coherent product experience.

Required primary navigation:

```text
Home
├── Memory
├── Intelligence
├── Decisions
├── Tasks and Goals
├── Timeline
├── Search
├── Workspaces
├── Integrations
├── Governance
└── Administration
```

The user must not need to understand:

- Event Bus internals;
- subscriber architecture;
- database models;
- routing structure;
- service boundaries;
- runtime implementation.

Customer-facing language must describe outcomes.

---

# 9. MLP Exclusions

The following are explicitly outside the first commercial MLP:

- autonomous multi-agent operations;
- distributed event brokers;
- event replay at scale;
- full enterprise knowledge graph;
- advanced predictive simulation;
- autonomous learning;
- organizational digital twin;
- broad connector marketplace;
- complex workflow designer;
- public application marketplace;
- advanced billing automation;
- government-grade sovereign deployment;
- full compliance certification;
- full mobile application.

These exclusions protect focus and reduce delivery risk.

---

# 10. Technical Foundations Already Available

The MLP is supported by existing CGMS foundations:

- Runtime Platform;
- Operator Console;
- Observability;
- Workspace Management;
- Connector Framework;
- Memory Engine;
- Memory Intelligence Engine;
- Enterprise Event Bus;
- Audit Subscriber;
- Persistence Layer;
- Commercial Layer;
- Release Engineering;
- Engineering Knowledge Base.

The MLP effort should prioritize integration, hardening, user experience, and evidence rather than rebuilding these foundations.

---

# 11. Remaining MLP Engineering Work

Priority work required before pilot:

## Priority 1 — Product Experience

- coherent primary navigation;
- knowledge-worker interface;
- executive dashboard;
- guided onboarding;
- consistent terminology;
- error-state design;
- empty-state design.

## Priority 2 — Security

- robust authentication;
- role-based access control;
- workspace isolation;
- secrets management;
- secure session handling;
- audit persistence;
- access logging.

## Priority 3 — Timeline and Audit

- persistent timeline;
- persistent audit store;
- user-facing audit view;
- event traceability.

## Priority 4 — Search and Retrieval

- stable semantic search;
- relevance explanation;
- filtering;
- retrieval performance;
- search quality tests.

## Priority 5 — Connectors

- select two pilot connectors;
- permission-aware ingestion;
- health monitoring;
- retry and failure handling;
- ingestion traceability.

## Priority 6 — Reliability

- production deployment guide;
- database migrations;
- backup and restore;
- structured logging;
- monitoring;
- operational runbooks.

---

# 12. Pilot Use Case

The recommended pilot use case is:

## Decision and Project Memory Continuity

The pilot organization selects one active department or project team.

CGMS captures:

- key decisions;
- action items;
- goals;
- major events;
- risks;
- lessons learned;
- project insights.

Users should be able to ask:

- Why was this decision made?
- What actions followed?
- What remains unresolved?
- What knowledge is becoming stale?
- What should a new team member know?
- Which memories are currently most important?
- What happened before the current situation?

---

# 13. Pilot Scope

Recommended pilot size:

- one organization;
- one department or programme;
- 15 to 50 users;
- one or two connectors;
- 8 to 12 weeks;
- controlled data scope;
- named executive sponsor;
- named operational owner;
- weekly feedback cycle.

The pilot must not attempt enterprise-wide rollout.

---

# 14. Pilot Success Criteria

The pilot is successful when:

## Adoption

- at least 70% of invited pilot users activate;
- at least 50% use CGMS weekly;
- at least 30% contribute or update memories.

## Knowledge Capture

- critical decisions are recorded;
- project actions and goals are linked;
- important institutional knowledge is preserved;
- users identify missing context through CGMS.

## Retrieval Value

- users retrieve useful prior context;
- search success is measurable;
- users report reduced time locating information;
- duplicate work is reduced.

## Intelligence Value

- users understand Memory Intelligence scores;
- stale and high-priority memories are surfaced;
- explainability is considered useful and credible.

## Governance

- important actions are auditable;
- access is appropriately controlled;
- pilot users report confidence in the system.

## Reliability

- no critical data loss;
- no unresolved high-severity security issue;
- platform availability meets the pilot commitment;
- connector failures are visible and recoverable.

---

# 15. Product Acceptance Criteria

The MLP is accepted only when:

1. all required workflows are implemented;
2. no critical regression test fails;
3. security review is complete;
4. workspace separation is verified;
5. audit persistence is operational;
6. selected connectors are production-ready;
7. onboarding is usable without developer assistance;
8. executive dashboard is functional;
9. search quality is validated;
10. pilot documentation is complete;
11. deployment is repeatable;
12. support procedures are documented;
13. Product Architecture is updated;
14. Platform Architecture is updated;
15. `CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md` is updated.

---

# 16. Commercial Validation Questions

The pilot must help answer:

- Will customers pay to reduce organizational knowledge loss?
- Which buyer owns the budget?
- Which workflow creates the strongest perceived value?
- Is Memory Intelligence understandable and trusted?
- Which connector is essential?
- Which user persona adopts fastest?
- Which dashboard metrics matter most?
- What deployment model is preferred?
- What security concerns block adoption?
- What pricing model is most credible?

---

# 17. Initial Pricing Hypotheses

Pricing is not approved at this stage.

Potential future models:

- per active user;
- per workspace;
- per organization;
- platform subscription plus connector add-ons;
- private deployment license;
- enterprise annual contract;
- research institution license.

Pricing must be validated through pilot conversations.

---

# 18. MLP Risks

## Product Risk

The product may appear too broad.

Mitigation:

- maintain one flagship workflow;
- limit navigation;
- use customer language;
- avoid exposing internal architecture.

## Adoption Risk

Users may not consistently capture knowledge.

Mitigation:

- connector-assisted capture;
- guided workflows;
- lightweight memory creation;
- visible user benefit.

## Trust Risk

Users may not trust scoring or recommendations.

Mitigation:

- explainability;
- visible evidence;
- user controls;
- transparent limitations.

## Security Risk

Organizations may reject the product without mature controls.

Mitigation:

- prioritize RBAC;
- workspace isolation;
- audit persistence;
- security documentation.

## Integration Risk

Connectors may be unreliable or permission-insensitive.

Mitigation:

- support only two connectors initially;
- implement health, retries, and traceability.

---

# 19. MLP Delivery Sequence

Recommended sequence:

1. lock target customer and pilot workflow;
2. define UX architecture;
3. complete persistent timeline and audit;
4. harden authentication and workspace isolation;
5. stabilize semantic search;
6. productionize two connectors;
7. build executive memory dashboard;
8. implement guided onboarding;
9. complete pilot deployment package;
10. recruit controlled pilot customer;
11. run pilot;
12. evaluate results;
13. revise product and pricing;
14. prepare first commercial release.

---

# 20. Milestone Governance

This document must be updated when:

- the first pilot customer is selected;
- the flagship workflow changes;
- the MLP scope changes;
- pilot success criteria change;
- new exclusions are approved;
- commercial readiness is achieved;
- pilot results are available.

At the completion of the MLP Definition milestone, update:

- `CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md`;
- Product Architecture Blueprint;
- Product Book;
- Platform Architecture Map;
- PMO Roadmap.

---

# 21. Immediate Next Milestone

The next approved productization milestone is:

# CGMS User Experience Architecture

It will define:

- primary personas;
- information architecture;
- navigation;
- page hierarchy;
- role-based experiences;
- key workflows;
- screen inventory;
- dashboard model;
- onboarding experience;
- user experience acceptance criteria.

---

# 22. MLP Decision

CGMS will not attempt to commercialize the entire Enterprise Cognitive Operating System vision at once.

The first commercial product will focus on one measurable promise:

> Preserve critical organizational knowledge and recover the context behind important decisions, actions, and events.

This scope remains binding unless changed through the approved governance process.
