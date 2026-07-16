# CGMS User Experience Architecture

## Enterprise Productization Milestone

**Product:** Contextual Group Memory System  
**Abbreviation:** CGMS  
**Strategic Phase:** Phase II – Enterprise Productization  
**Current Engineering Baseline:** CGMS v1.75 – Enterprise Event Bus  
**Current Product Baseline:** CGMS Minimum Lovable Product  
**Document Owner:** Product Experience Architecture  
**Status:** Approved UX Architecture  
**Document Type:** Living Product Artifact

---

# 1. Purpose

This document defines how users should experience CGMS.

It translates the Product Architecture and Minimum Lovable Product into:

- user roles;
- navigation;
- page hierarchy;
- information architecture;
- role-based experiences;
- flagship workflows;
- dashboard structure;
- onboarding;
- interaction principles;
- screen inventory;
- user experience acceptance criteria.

The platform architecture defines how CGMS works internally.

The product architecture defines what value CGMS creates.

The user experience architecture defines how users access that value.

---

# 2. UX Vision

CGMS should feel like an institutional intelligence workspace, not a collection of technical modules.

The experience should help users answer five questions quickly:

1. What matters now?
2. What happened before?
3. Why was this decision made?
4. What remains unresolved?
5. What knowledge is at risk of being lost?

The product should reduce cognitive load rather than expose system complexity.

---

# 3. UX Principles

## 3.1 Outcome-First

Every page must help a user complete a meaningful job.

## 3.2 Context Before Volume

CGMS should not overwhelm users with raw information. It should prioritize context, relationships, and relevance.

## 3.3 Explainability by Default

Scores, recommendations, and relationships should be explainable.

## 3.4 Progressive Disclosure

Simple tasks should remain simple. Advanced controls should appear only when required.

## 3.5 Role Relevance

Different users should see different priorities without creating entirely separate products.

## 3.6 Consistency

Memory types, statuses, priorities, filters, and actions should behave consistently throughout the product.

## 3.7 Trust and Control

Users should understand:

- what CGMS captured;
- where it came from;
- why it matters;
- who can access it;
- what action occurred;
- how to correct or override it.

## 3.8 Accessibility

The product should support:

- keyboard navigation;
- readable contrast;
- clear labels;
- screen-reader-compatible controls;
- non-colour-only status indicators;
- responsive layouts.

---

# 4. Primary User Roles

## 4.1 Knowledge Worker

Primary jobs:

- capture knowledge;
- retrieve prior context;
- connect tasks, goals, decisions, and events;
- understand what matters;
- avoid duplicated work.

Default landing experience:

- My priorities;
- recent memories;
- unresolved tasks;
- recent decisions;
- suggested related context.

## 4.2 Team Leader

Primary jobs:

- maintain team continuity;
- review unresolved actions;
- inspect team memory health;
- identify stale or high-risk knowledge;
- preserve decision rationale.

Default landing experience:

- team memory health;
- unresolved decisions;
- overdue tasks;
- high-priority memories;
- recent team activity.

## 4.3 Executive

Primary jobs:

- understand major developments;
- identify risks;
- review key decisions;
- monitor institutional memory health;
- trace insight to evidence.

Default landing experience:

- executive briefing;
- strategic decisions;
- emerging risks;
- memory health indicators;
- major unresolved actions.

## 4.4 Administrator

Primary jobs:

- manage users and workspaces;
- configure integrations;
- set quotas;
- manage access;
- monitor adoption.

Default landing experience:

- workspace status;
- user activity;
- connector status;
- security alerts;
- usage metrics.

## 4.5 Operator

Primary jobs:

- monitor system health;
- inspect event activity;
- manage runtime controls;
- investigate failures;
- enforce quarantine or kill switch.

Default landing experience:

- health status;
- event failures;
- runtime timeline;
- connector incidents;
- operator actions.

## 4.6 Researcher

Primary jobs:

- preserve research context;
- connect evidence and findings;
- trace methodology;
- maintain contribution lineage;
- recover prior research decisions.

Default landing experience:

- active research threads;
- recent findings;
- unresolved questions;
- evidence relationships;
- publication progress.

---

# 5. Information Architecture

Recommended product hierarchy:

```text
CGMS
├── Home
├── Memory
│   ├── All Memories
│   ├── Decisions
│   ├── Tasks
│   ├── Goals
│   ├── Events
│   └── Insights
├── Intelligence
│   ├── Memory Health
│   ├── Priority Intelligence
│   ├── Freshness
│   ├── Confidence
│   └── Explanations
├── Timeline
├── Search
├── Workspaces
├── Integrations
├── Governance
│   ├── Audit
│   ├── Access
│   ├── Policies
│   └── Decision Lineage
├── Operations
│   ├── Health
│   ├── Runtime
│   ├── Events
│   ├── Incidents
│   └── Controls
└── Administration
    ├── Users
    ├── Roles
    ├── Quotas
    ├── Plans
    └── Settings
```

---

# 6. Global Navigation Model

## 6.1 Primary Navigation

Always visible:

- Home
- Memory
- Intelligence
- Timeline
- Search

Role-dependent:

- Workspaces
- Integrations
- Governance
- Operations
- Administration

## 6.2 Global Utilities

Always available:

- workspace switcher;
- global search;
- quick capture;
- notifications;
- help;
- user profile.

## 6.3 Quick Capture

The quick-capture action should allow a user to create:

- memory;
- decision;
- task;
- goal;
- event;
- insight.

The user should not need to navigate away from the current page.

---

# 7. Home Experience

The Home page should answer:

- What needs my attention?
- What changed?
- What should I know?
- What remains unresolved?
- What does CGMS recommend I review?

Recommended sections:

## 7.1 Priority Summary

- high-priority memories;
- urgent tasks;
- unresolved decisions;
- stale critical knowledge.

## 7.2 Recent Activity

- newly created memories;
- updated decisions;
- completed tasks;
- new connector activity.

## 7.3 Intelligence Summary

- memory health;
- freshness warnings;
- confidence issues;
- notable score changes.

## 7.4 Suggested Context

- related memories;
- relevant prior decisions;
- recurring issues;
- knowledge gaps.

## 7.5 Workspace Pulse

- active users;
- recent contributions;
- unresolved work;
- connector status.

---

# 8. Memory Experience

## 8.1 Memory List

Required elements:

- title;
- type;
- status;
- owner;
- priority;
- composite score;
- freshness;
- updated date;
- workspace.

Required filters:

- memory type;
- status;
- priority;
- score range;
- freshness;
- owner;
- workspace;
- date range.

Required actions:

- open;
- edit;
- complete;
- reopen;
- delay;
- restore;
- reprioritize;
- archive where appropriate.

## 8.2 Memory Detail

Required sections:

- title and summary;
- memory type;
- status;
- owner;
- source;
- timestamps;
- Memory Intelligence score;
- explanation;
- related memories;
- linked decisions;
- linked tasks and goals;
- timeline;
- audit trail;
- available actions.

## 8.3 Memory Creation

Required fields:

- title;
- content;
- memory type;
- priority;
- owner;
- workspace;
- optional relationships;
- optional due date;
- optional source reference.

Creation should be possible in under one minute for a basic memory.

---

# 9. Intelligence Experience

The Intelligence area should translate scoring into understandable organizational meaning.

## 9.1 Memory Health

Show:

- overall memory health;
- critical memories;
- stale memories;
- low-confidence memories;
- unowned memories;
- unresolved high-priority items.

## 9.2 Explanation Panel

For each score, explain:

- factor;
- current value;
- contribution to composite score;
- supporting evidence;
- recommended action where applicable.

## 9.3 Trend View

Show:

- score movement over time;
- priority changes;
- freshness decline;
- confidence improvement or deterioration;
- memory volume by type.

## 9.4 Actionable Intelligence

Surface recommendations such as:

- review this stale decision;
- assign an owner;
- connect this memory to a goal;
- resolve conflicting information;
- preserve knowledge before a transition.

---

# 10. Decision Experience

A decision record should include:

- decision title;
- decision statement;
- rationale;
- owner;
- date;
- participants;
- alternatives considered;
- supporting evidence;
- linked tasks;
- linked goals;
- expected outcome;
- actual outcome;
- review date;
- status.

The decision page must answer:

- What was decided?
- Why?
- Based on what evidence?
- Who was responsible?
- What happened next?
- Was the decision successful?

---

# 11. Timeline Experience

The Timeline should provide chronological organizational context.

Required capabilities:

- filter by workspace;
- filter by memory type;
- filter by user;
- filter by date;
- highlight major decisions;
- show lifecycle actions;
- show event sources;
- expand event details;
- navigate to related memory.

The Timeline should support both:

- operational timeline;
- memory-specific timeline.

---

# 12. Search Experience

Search must support:

- natural-language queries;
- keyword search;
- filters;
- workspace scope;
- memory type;
- status;
- date;
- relevance explanation.

Each result should show:

- title;
- memory type;
- summary;
- relevance reason;
- score;
- freshness;
- source;
- updated date.

The user should be able to refine without restarting the search.

---

# 13. Workspace Experience

Required capabilities:

- workspace switcher;
- workspace overview;
- members;
- roles;
- quotas;
- metrics;
- integrations;
- recent activity;
- memory health.

Workspace context should remain visible throughout the application.

---

# 14. Integration Experience

Required sections:

- available connectors;
- active connectors;
- health status;
- last successful ingestion;
- last failure;
- permission status;
- ingestion activity;
- retry controls;
- disconnect action.

Connector setup should include:

1. choose connector;
2. authenticate;
3. choose scope;
4. review permissions;
5. confirm;
6. test connection;
7. activate.

---

# 15. Governance Experience

## 15.1 Audit

Show:

- event;
- source;
- actor;
- workspace;
- timestamp;
- result;
- correlation identifier;
- related memory.

## 15.2 Access

Show:

- users;
- roles;
- workspace permissions;
- exceptions;
- recent access changes.

## 15.3 Policies

Show:

- active policies;
- enforcement status;
- violations;
- exceptions;
- review dates.

## 15.4 Decision Lineage

Show:

- decision;
- evidence;
- related memories;
- dependent tasks;
- outcomes;
- changes over time.

---

# 16. Operations Experience

Required sections:

- system health;
- event activity;
- errors;
- latency;
- runtime commands;
- feature flags;
- quarantine;
- kill switch;
- connector health;
- incident timeline.

Dangerous controls should require:

- clear confirmation;
- reason;
- actor identity;
- audit record.

---

# 17. Administration Experience

Required sections:

- users;
- roles;
- workspaces;
- plans;
- quotas;
- security;
- settings;
- deployment information.

Administration should be separated from everyday knowledge-worker tasks.

---

# 18. Onboarding Experience

The onboarding flow should be role-aware.

## Step 1: Welcome

Explain CGMS in customer language.

## Step 2: Select Workspace

Create or join a workspace.

## Step 3: Choose Role

- knowledge worker;
- team leader;
- executive;
- administrator;
- operator;
- researcher.

## Step 4: Connect a Source

Optional during first session.

## Step 5: Create First Memory

Guided example.

## Step 6: View First Score

Explain Memory Intelligence.

## Step 7: Search and Retrieve

Demonstrate value.

## Step 8: Complete Setup

Show recommended next actions.

A new user should reach the first meaningful outcome within 10 minutes.

---

# 19. Screen Inventory

Minimum MLP screen inventory:

1. Login
2. Onboarding
3. Home
4. Memory List
5. Memory Detail
6. Create Memory
7. Edit Memory
8. Intelligence Dashboard
9. Explanation Detail
10. Decision List
11. Decision Detail
12. Task and Goal View
13. Timeline
14. Search Results
15. Workspace Overview
16. Workspace Members
17. Integrations
18. Connector Setup
19. Governance Audit
20. Operations Health
21. Runtime Controls
22. Administration Users
23. Administration Settings

---

# 20. Role-Based Access to Navigation

| Area | Knowledge Worker | Team Leader | Executive | Administrator | Operator | Researcher |
|---|---:|---:|---:|---:|---:|---:|
| Home | Yes | Yes | Yes | Yes | Yes | Yes |
| Memory | Yes | Yes | View | Yes | View | Yes |
| Intelligence | Yes | Yes | Yes | Yes | Yes | Yes |
| Timeline | Yes | Yes | Yes | Yes | Yes | Yes |
| Search | Yes | Yes | Yes | Yes | Yes | Yes |
| Workspaces | Limited | Limited | View | Yes | View | Limited |
| Integrations | No | No | No | Yes | Yes | No |
| Governance | Limited | Limited | View | Yes | Yes | Limited |
| Operations | No | No | No | Limited | Yes | No |
| Administration | No | No | No | Yes | Limited | No |

Final access must be enforced by backend authorization, not only hidden navigation.

---

# 21. Dashboard Model

## 21.1 Knowledge Worker Dashboard

- my tasks;
- recent memories;
- suggested context;
- high-priority items;
- recent decisions.

## 21.2 Team Leader Dashboard

- team memory health;
- unresolved tasks;
- stale knowledge;
- decision status;
- contribution activity.

## 21.3 Executive Dashboard

- strategic decisions;
- institutional memory health;
- emerging risks;
- unresolved actions;
- high-impact developments.

## 21.4 Administrator Dashboard

- users;
- workspaces;
- connectors;
- quotas;
- security events;
- adoption metrics.

## 21.5 Operator Dashboard

- health;
- errors;
- latency;
- event failures;
- runtime state;
- incidents.

---

# 22. Interaction Standards

## 22.1 Status Language

Use clear terms:

- Active
- Completed
- Delayed
- Reopened
- Archived
- Restored

## 22.2 Priority Language

Use:

- Low
- Medium
- High
- Critical

## 22.3 Feedback

Every user action should provide:

- success confirmation;
- failure reason;
- next action where appropriate.

## 22.4 Destructive Actions

Require confirmation and explanation.

## 22.5 Empty States

Each empty state should explain:

- what belongs here;
- why it matters;
- how to create the first item.

---

# 23. UX Metrics

Measure:

- time to first memory;
- time to first successful search;
- search success rate;
- task completion rate;
- weekly active users;
- memory contribution rate;
- onboarding completion;
- feature adoption;
- user-reported time saved;
- executive dashboard usage;
- connector setup success.

---

# 24. UX Acceptance Criteria

The UX Architecture milestone is accepted when:

1. primary roles are defined;
2. navigation is approved;
3. screen inventory is complete;
4. flagship workflow is represented;
5. onboarding is defined;
6. role-based experiences are mapped;
7. executive, user, administrator, and operator views are distinct;
8. accessibility principles are documented;
9. customer-facing terminology is consistent;
10. MLP scope remains intact;
11. Product Architecture is updated where required;
12. `CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md` is updated.

---

# 25. Immediate Next Milestone

The next approved milestone is:

# CGMS Product Navigation and Page Architecture

It should translate this UX Architecture into:

- route map;
- page hierarchy;
- navigation components;
- dashboard layout;
- page responsibilities;
- current-page mapping;
- future-page backlog;
- frontend implementation sequence.

---

# 26. UX Decision

CGMS will not expose its internal technical architecture as the primary user experience.

Users will interact with customer outcomes:

- memory;
- intelligence;
- decisions;
- actions;
- timeline;
- governance;
- operations.

This decision remains binding unless changed through the approved governance process.
