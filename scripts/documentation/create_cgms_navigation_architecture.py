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
    / "CGMS_Product_Navigation_and_Page_Architecture.md"
)

CONTENT = r"""# CGMS Product Navigation and Page Architecture

## Enterprise Productization Milestone

**Product:** Contextual Group Memory System  
**Abbreviation:** CGMS  
**Strategic Phase:** Phase II – Enterprise Productization  
**Current Engineering Baseline:** CGMS v1.75 – Enterprise Event Bus  
**Current Product Baseline:** Minimum Lovable Product  
**Document Owner:** Product Experience Architecture  
**Status:** Approved Navigation and Page Architecture  
**Document Type:** Living Product Artifact

---

# 1. Purpose

This document translates the approved CGMS User Experience Architecture into a concrete navigation model, route map, page hierarchy, page responsibilities, dashboard structure, and frontend implementation sequence.

It defines:

- global navigation;
- role-based navigation;
- route structure;
- page hierarchy;
- page responsibilities;
- current-page mapping;
- future-page backlog;
- dashboard composition;
- interaction boundaries;
- implementation priorities;
- acceptance criteria.

---

# 2. Navigation Principles

CGMS navigation must:

- expose customer outcomes rather than internal modules;
- remain consistent across roles;
- support workspace context;
- reduce visual pressure;
- support progressive disclosure;
- preserve clear separation between daily work, governance, and operations;
- remain scalable as new product pillars are introduced.

---

# 3. Primary Navigation

Recommended primary navigation:

```text
Home
Memory
Intelligence
Decisions
Tasks & Goals
Timeline
Search
```

Role-based secondary navigation:

```text
Workspaces
Integrations
Governance
Operations
Administration
```

Global utilities:

```text
Workspace Switcher
Quick Capture
Global Search
Notifications
Help
User Profile
```

---

# 4. Route Map

Recommended frontend routes:

```text
/
├── /home
├── /memory
│   ├── /all
│   ├── /tasks
│   ├── /goals
│   ├── /events
│   ├── /decisions
│   ├── /insights
│   ├── /new
│   └── /[memory_id]
├── /intelligence
│   ├── /overview
│   ├── /memory-health
│   ├── /priority
│   ├── /freshness
│   ├── /confidence
│   └── /explanations/[memory_id]
├── /decisions
│   ├── /all
│   ├── /new
│   └── /[decision_id]
├── /tasks
│   ├── /all
│   ├── /my
│   ├── /overdue
│   └── /[task_id]
├── /goals
│   ├── /all
│   ├── /active
│   └── /[goal_id]
├── /timeline
├── /search
├── /workspaces
│   ├── /overview
│   ├── /members
│   ├── /metrics
│   ├── /quotas
│   └── /settings
├── /integrations
│   ├── /available
│   ├── /active
│   ├── /health
│   └── /[connector_id]
├── /governance
│   ├── /audit
│   ├── /access
│   ├── /policies
│   └── /decision-lineage
├── /operations
│   ├── /health
│   ├── /runtime
│   ├── /events
│   ├── /incidents
│   ├── /flags
│   ├── /quarantine
│   └── /kill-switch
└── /admin
    ├── /users
    ├── /roles
    ├── /plans
    ├── /security
    └── /settings
```

---

# 5. Shell Layout

The application shell should include:

```text
Top Bar
├── Workspace Switcher
├── Global Search
├── Quick Capture
├── Notifications
└── User Menu

Left Navigation
├── Core Navigation
├── Role-Based Navigation
└── Collapsible Sections

Main Content
├── Page Header
├── Page Sub-header
├── Filters / Actions
└── Page Body

Context Panel
├── Related Memory
├── Explanation
├── Timeline
└── Audit
```

The right-side context panel should be optional and collapsible.

---

# 6. Home Page Architecture

Route:

```text
/home
```

Page responsibility:

- summarize what matters now;
- surface recent changes;
- show unresolved actions;
- present recommended context;
- adapt to user role.

Recommended sections:

1. Attention Required
2. Recent Activity
3. Memory Intelligence Summary
4. Recent Decisions
5. Tasks and Goals
6. Suggested Context
7. Workspace Pulse

Role variants:

- Knowledge Worker: personal actions and recent context
- Team Leader: team health and unresolved work
- Executive: strategic decisions, risks, and memory health
- Administrator: adoption, connectors, and security
- Operator: system health and incidents

---

# 7. Memory Pages

## 7.1 Memory List

Route:

```text
/memory/all
```

Responsibilities:

- browse;
- filter;
- sort;
- open;
- bulk select;
- create memory.

Columns:

- title;
- type;
- status;
- owner;
- priority;
- composite score;
- freshness;
- updated date.

## 7.2 Memory Detail

Route:

```text
/memory/[memory_id]
```

Responsibilities:

- display complete memory context;
- show score and explanation;
- show relationships;
- expose lifecycle actions;
- show timeline and audit.

Tabs:

```text
Overview
Relationships
Intelligence
Timeline
Audit
```

## 7.3 Create Memory

Route:

```text
/memory/new
```

Responsibilities:

- create structured memory quickly;
- support templates by memory type;
- validate required fields;
- preserve source context.

---

# 8. Intelligence Pages

## 8.1 Intelligence Overview

Route:

```text
/intelligence/overview
```

Sections:

- overall memory health;
- score distribution;
- high-priority memories;
- stale memories;
- low-confidence memories;
- recent score changes.

## 8.2 Memory Health

Route:

```text
/intelligence/memory-health
```

Responsibilities:

- show institutional memory health;
- identify risk areas;
- support workspace and type filters.

## 8.3 Explanation Detail

Route:

```text
/intelligence/explanations/[memory_id]
```

Responsibilities:

- explain score factors;
- show contribution of each factor;
- show evidence;
- show recommended actions.

---

# 9. Decisions Pages

## 9.1 Decision List

Route:

```text
/decisions/all
```

Columns:

- title;
- owner;
- date;
- status;
- outcome;
- linked goals;
- review date.

## 9.2 Decision Detail

Route:

```text
/decisions/[decision_id]
```

Sections:

- decision statement;
- rationale;
- alternatives;
- evidence;
- participants;
- actions;
- outcomes;
- timeline;
- related memories.

---

# 10. Tasks and Goals Pages

Tasks and goals should share interaction patterns.

Required capabilities:

- list;
- filters;
- ownership;
- status;
- due date;
- dependencies;
- linked decisions;
- linked memories;
- progress.

Task routes:

```text
/tasks/all
/tasks/my
/tasks/overdue
/tasks/[task_id]
```

Goal routes:

```text
/goals/all
/goals/active
/goals/[goal_id]
```

---

# 11. Timeline Page

Route:

```text
/timeline
```

Responsibilities:

- display chronological organizational context;
- filter by workspace, type, user, and date;
- highlight major events;
- navigate to related records.

Views:

```text
Organization
Workspace
Memory
User
```

---

# 12. Search Page

Route:

```text
/search
```

Responsibilities:

- accept natural-language and keyword queries;
- display relevant memories;
- explain relevance;
- support refinement.

Required components:

- query input;
- recent searches;
- filter panel;
- result list;
- relevance explanation;
- related context;
- saved search option.

---

# 13. Workspace Pages

Routes:

```text
/workspaces/overview
/workspaces/members
/workspaces/metrics
/workspaces/quotas
/workspaces/settings
```

Responsibilities:

- maintain workspace context;
- manage members;
- monitor activity;
- configure quotas;
- manage settings.

---

# 14. Integration Pages

Routes:

```text
/integrations/available
/integrations/active
/integrations/health
/integrations/[connector_id]
```

Connector detail page must show:

- status;
- authentication state;
- permission scope;
- last successful ingestion;
- last failure;
- event volume;
- retry action;
- deactivate action.

---

# 15. Governance Pages

Routes:

```text
/governance/audit
/governance/access
/governance/policies
/governance/decision-lineage
```

Audit page must support:

- filtering;
- event inspection;
- correlation ID;
- source;
- actor;
- workspace;
- related memory.

---

# 16. Operations Pages

Routes:

```text
/operations/health
/operations/runtime
/operations/events
/operations/incidents
/operations/flags
/operations/quarantine
/operations/kill-switch
```

Operations pages must remain restricted to authorized roles.

Dangerous controls require:

- explicit confirmation;
- reason;
- user identity;
- audit record.

---

# 17. Administration Pages

Routes:

```text
/admin/users
/admin/roles
/admin/plans
/admin/security
/admin/settings
```

Administration must be visually separated from daily work.

---

# 18. Current-to-Future Page Mapping

Current existing route areas include:

- operator console;
- runtime commands;
- runtime events;
- runtime metrics;
- runtime policy;
- runtime quarantine;
- workspace administration;
- workspace metrics;
- connector health;
- external ingestion;
- memory intelligence;
- memory graph;
- memory actions;
- release status;
- system health.

These should be mapped into the new product architecture instead of exposed as isolated route pages.

Example mapping:

| Current Route Area | Product Destination |
|---|---|
| memory_intelligence | Intelligence |
| memory_actions | Memory Detail |
| memory_graph | Memory Relationships |
| runtime_metrics | Operations Health |
| runtime_events | Operations Events |
| runtime_policy | Governance Policies |
| runtime_quarantine | Operations Quarantine |
| workspace_admin | Workspaces |
| connector_health | Integrations Health |
| audit_console | Governance Audit |
| operator_console | Operations Overview |

---

# 19. Page Header Standard

Every primary page should include:

- page title;
- one-line purpose statement;
- primary action;
- optional filters;
- status indicator where relevant.

Example:

```text
Memory Intelligence
Understand what knowledge matters, why it matters, and where attention is required.
[Review Critical Memories]
```

---

# 20. Visual Density Standard

To reduce visual pressure:

- no more than five primary cards above the fold;
- use tabs for related detail;
- use collapsible filters;
- use progressive disclosure;
- avoid exposing raw system fields by default;
- reserve dense tables for administrative and operator views.

---

# 21. Dashboard Layout Standard

Recommended dashboard structure:

```text
Header
Summary Metrics
Primary Insight
Priority Actions
Recent Activity
Secondary Analysis
```

Dashboards should not become collections of unrelated widgets.

Each dashboard must tell one coherent story.

---

# 22. Component Architecture

Recommended shared frontend components:

```text
AppShell
TopBar
SideNavigation
WorkspaceSwitcher
QuickCapture
PageHeader
MetricCard
StatusBadge
PriorityBadge
MemoryScore
ExplanationPanel
TimelineList
RelationshipPanel
FilterPanel
EmptyState
ErrorState
ConfirmationDialog
AuditTable
ConnectorHealthCard
```

---

# 23. Frontend Implementation Sequence

Recommended sequence:

1. application shell;
2. navigation;
3. Home;
4. Memory List;
5. Memory Detail;
6. Intelligence Overview;
7. Search;
8. Timeline;
9. Decisions;
10. Tasks and Goals;
11. Workspaces;
12. Integrations;
13. Governance;
14. Operations;
15. Administration;
16. onboarding;
17. responsive and accessibility hardening.

---

# 24. Navigation Acceptance Criteria

This milestone is accepted when:

1. primary navigation is approved;
2. route map is complete;
3. page responsibilities are defined;
4. current routes are mapped;
5. role-based navigation is documented;
6. dashboard standards are defined;
7. screen density principles are defined;
8. component architecture is defined;
9. frontend implementation sequence is approved;
10. UX Architecture remains aligned;
11. MLP scope remains intact;
12. `CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md` is updated at milestone closure.

---

# 25. Immediate Next Milestone

The next approved milestone is:

# CGMS Product Capability and Feature Prioritization Matrix

It will classify each capability by:

- customer value;
- commercial importance;
- technical readiness;
- security dependency;
- MLP inclusion;
- pilot inclusion;
- release target;
- current implementation status.

---

# 26. Navigation Decision

CGMS will organize the customer experience around outcomes and user jobs, not technical modules.

The approved navigation and route architecture remains binding unless changed through the approved governance process.
"""


def main() -> None:
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_FILE.write_text(CONTENT.strip() + "\n", encoding="utf-8")

    print("CGMS Product Navigation and Page Architecture created successfully.")
    print(f"Path: {TARGET_FILE}")
    print(f"Characters written: {len(CONTENT):,}")


if __name__ == "__main__":
    main()
