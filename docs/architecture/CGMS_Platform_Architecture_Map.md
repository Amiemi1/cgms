CGMS Platform Architecture Map
Master Blueprint for the Enterprise Cognitive Operating System
Baseline: CGMS v1.75
Current Platform State: Enterprise Event Bus Foundation
Purpose: Define the canonical map of CGMS subsystems, bounded contexts, dependencies, event flows, documentation artifacts, and future platform evolution.

1. Platform Vision
CGMS is an Enterprise Cognitive Operating System designed to provide:

persistent organizational memory
contextual intelligence
explainable reasoning
enterprise knowledge orchestration
event-driven processing
auditability
decision support
long-term organizational memory preservation

CGMS is not a chatbot. It is a cognitive infrastructure platform.

2. Current Platform Pillars
CGMS Platform
│
├── Runtime Platform
├── Operator Console
├── Observability
├── Workspace Management
├── Connector Framework
├── Memory Engine
├── Memory Intelligence Engine
├── Enterprise Event Bus
├── Security & Governance
├── Product / Commercial Layer
├── Research & Documentation Knowledge Base
└── Future Documentation Intelligence Framework


3. Current Bounded Contexts
app/services/
│
├── memory
├── memory_intelligence
├── orchestration
├── workspace
├── connectors
├── runtime / dashboard runtime
├── intelligence
├── reasoning
├── retrieval
├── security
├── governance
├── commercial
├── product
├── timeline
├── graph
├── scheduler
├── ingestion
├── detection
├── explainability
└── future documentation


4. Core Dependency Direction
Approved direction:
Routes
  ↓
Application / Domain Services
  ↓
Domain Events
  ↓
Enterprise Event Bus
  ↓
Subscribers

Forbidden direction:
Route
  ↓
Directly call many downstream services

The Event Bus is now the preferred integration mechanism for cross-domain side effects.

5. Enterprise Event Bus Position
Domain Service
     │
     ▼
DomainEvent
     │
     ▼
EnterpriseEventBus
     │
 ┌───┼────────────┬─────────────┬─────────────┐
 ▼   ▼            ▼             ▼             ▼
Memory Intelligence
Audit
Timeline
Knowledge Graph
Future AI Services

Current implemented subscribers:
✔ Memory Intelligence Subscriber
✔ Audit Subscriber

Future subscribers:
Timeline Subscriber
Workspace Subscriber
Runtime Subscriber
Connector Subscriber
Knowledge Graph Subscriber
Notification Subscriber
AI Reasoning Subscriber
Documentation Intelligence Subscriber


6. Event Bus Components
app/services/orchestration/
│
├── domain_event.py
├── dispatch_result.py
├── event_registry.py
├── event_bus.py
├── bootstrap.py
├── contracts/
│   ├── memory_events.py
│
└── subscribers/
    ├── audit_subscriber.py

Responsibilities:



Component
Responsibility




DomainEvent
Canonical immutable event envelope


EventRegistry
Maps event names to subscribers


EnterpriseEventBus
Dispatches events and collects results


DispatchResult
Captures dispatch outcome and observability metadata


Contracts
Standard event names and event factories


Bootstrap
Registers default platform subscribers


Subscribers
React to domain events independently




7. Memory Flow After v1.75
Memory Action Route
      ↓
Database Commit
      ↓
memory.priority_changed
      ↓
EnterpriseEventBus
      ↓
Memory Intelligence Subscriber
      ↓
process_memory_event()
      ↓
calculate_memory_score()
      ↓
save_score()

Audit also receives the same event independently.

8. Documentation Knowledge Base
The CGMS Knowledge Base consists of:
Engineering Handbook
Architecture Bible
Product Book
Research Companion
Release Archive
Engineering Release Dossiers
PMO Roadmap
API Inventory
Technical Debt Register
Event Catalog

Purpose mapping:



Artifact
Purpose




Engineering Handbook
How CGMS is built, tested, and operated


Architecture Bible
Why CGMS is designed this way


Product Book
What CGMS is and where it is going


Research Companion
How CGMS contributes to research


Release Archive
What changed in every release


Event Catalog
Canonical record of domain events


API Inventory
Public/internal API surface


Technical Debt Register
Known risks and planned remediation




9. Future Documentation Intelligence Framework
Proposed bounded context:
app/services/documentation/
│
├── models/
├── generators/
├── repository/
├── templates/
└── services/

Purpose:

generate release notes
generate release dossiers
update API inventory
update technical debt register
map features to releases
map ADRs to implementation
map research contributions to architecture
preserve engineering memory

Documentation Intelligence will eventually subscribe to Event Bus events such as:
release.completed
api.changed
adr.created
test.completed
technical_debt.created


10. Current Technical Debt
TD-v1.75-001
FastAPI @app.on_event startup hook is deprecated.
Target: migrate to lifespan handler in v1.76.

TD-v1.75-002
Some synchronous publishing paths remain.
Target: convert to native async in v1.76.

TD-v1.75-003
Legacy orchestration compatibility remains in EventRegistry.publish().
Target: migrate legacy event_router usage to EnterpriseEventBus directly.


11. v1.76 Candidate Roadmap
Recommended next platform milestone:
CGMS v1.76 — Platform Hardening and Documentation Intelligence Foundation

Priority sequence:

Migrate FastAPI startup to lifespan.
Remove legacy event_registry.publish() dependency.
Convert sync event publishing paths to native async.
Add Timeline Subscriber.
Add Runtime Event Contracts.
Add Workspace Event Contracts.
Create Documentation Intelligence Framework skeleton.
Generate first automated release documentation package.


12. Architecture Principle Going Forward
Every new CGMS capability must answer:
Which bounded context owns this?
Which domain events does it publish?
Which events does it subscribe to?
Which documentation artifacts must be updated?
Which tests prove it works?
Which research contribution does it support?

This keeps CGMS aligned with its long-term goal: becoming an enterprise-grade cognitive operating system.
