# CGMS v2.0 Domain Model & Enterprise Architecture Specification

## Document Control

| Item | Detail |
|---|---|
| Product | Contextual Group Memory System |
| Version | v2.0 Architecture Baseline |
| Status | Draft |
| Owner | Murphy Oboh |
| Architecture Gate | G2 |
| Related ADRs | ADR-001, ADR-002 |

## Purpose

This document defines the enterprise domain model, bounded contexts, service boundaries, event taxonomy, and architectural principles for CGMS v2.0.

CGMS v2.0 is designed as an Enterprise Cognitive Memory Platform that captures, understands, governs, and reasons over organizational knowledge across conversations, documents, applications, and enterprise workflows.

## Architecture Vision

CGMS is the operating system for organizational memory.

It transforms transient collaboration signals into persistent, explainable, governed, and actionable enterprise knowledge.

## Core Domains

1. Memory Domain
2. Workspace Domain
3. Connector Domain
4. Event Domain
5. Intelligence Domain
6. Knowledge Graph Domain
7. Governance Domain
8. Operator Domain
9. Commercial Domain
10. Research Domain

## Architecture Principles

1. Explainability First
2. Event-Driven by Default
3. Intelligence as a Service
4. Workspace-Aware Execution
5. Governance Embedded in Runtime
6. Backward Compatibility
7. Research-to-Product Traceability
8. Modular Extension
9. Observable Operations
10. Commercial Readiness

---

# 1. Bounded Contexts

CGMS v2.0 is organised into bounded contexts. Each context owns a specific part of the platform model and exposes capabilities through services, events, and APIs.

## 1.1 Memory Context

**Purpose:**  
Captures and manages structured organizational memory extracted from conversations, documents, connector events, and user actions.

**Owns:**
- Memory records
- Memory type
- Memory status
- Memory lifecycle
- Memory metadata
- Memory relationships
- Memory history

**Does not own:**
- Scoring algorithms
- Workspace permissions
- Connector authentication
- Commercial usage plans

---

## 1.2 Workspace Context

**Purpose:**  
Provides tenant and organizational boundaries for all CGMS activity.

**Owns:**
- Workspace registry
- Workspace context
- Workspace metrics
- Workspace status
- Workspace suspension
- Workspace-level quotas

**Does not own:**
- Global license plans
- Memory scoring
- Connector event parsing

---

## 1.3 Connector Context

**Purpose:**  
Normalizes external platform signals into CGMS-compatible events.

**Owns:**
- Connector registry
- Connector status
- Connector activation
- Connector health
- Adapter contracts
- External ingestion

**Does not own:**
- Memory scoring
- Workspace policy decisions
- Long-term event storage

---

## 1.4 Event Context

**Purpose:**  
Defines the event-driven backbone of CGMS.

**Owns:**
- Runtime events
- External events
- Audit events
- Timeline events
- Incident events
- Event routing contracts

**Does not own:**
- UI rendering
- Commercial billing
- AI reasoning

---

## 1.5 Intelligence Context

**Purpose:**  
Evaluates, scores, ranks, and explains memory value.

**Owns:**
- Importance score
- Confidence score
- Freshness score
- Priority score
- Composite Memory Intelligence Score
- Explainability factors
- Score recalculation rules

**Does not own:**
- Raw memory creation
- Workspace registration
- Connector ingestion

---

## 1.6 Knowledge Graph Context

**Purpose:**  
Connects memories, people, projects, decisions, tasks, documents, and events into a navigable organizational graph.

**Owns:**
- Nodes
- Edges
- Relationship types
- Graph traversal
- Graph-based discovery
- Contextual relationship mapping

**Does not own:**
- Memory scoring formulas
- User authentication
- Billing

---

## 1.7 Governance Context

**Purpose:**  
Controls safe, compliant, and auditable operation of CGMS.

**Owns:**
- Runtime policies
- Quarantine
- Kill switch
- Audit records
- RBAC
- Data retention
- Workspace suspension
- Compliance rules

**Does not own:**
- Product pricing
- UI layout
- Memory extraction logic

---

## 1.8 Operator Context

**Purpose:**  
Provides operational visibility and control.

**Owns:**
- Operator console
- Runtime health
- Timeline visibility
- Error visibility
- Runtime actions
- Observability endpoints

**Does not own:**
- Scoring algorithms
- Connector contracts
- Memory persistence

---

## 1.9 Commercial Context

**Purpose:**  
Packages CGMS as a product.

**Owns:**
- Plans
- Licenses
- Usage metering
- Quotas
- Commercial enforcement
- Product readiness

**Does not own:**
- Enterprise memory semantics
- Connector adapters
- Research outputs

---

## 1.10 Research Context

**Purpose:**  
Connects CGMS engineering outputs to academic research contributions.

**Owns:**
- ADR register
- Research themes
- Evaluation metrics
- Publications tracker
- Experimental design
- Evidence mapping

**Does not own:**
- Runtime service behavior
- Production incident management

---

# 2. Enterprise Domain Model

The Enterprise Domain Model defines the core business entities managed by CGMS.

Every entity has a clear owner, lifecycle, relationships, and responsibilities.

---

# 2.1 Memory

Memory is the fundamental asset of CGMS.

It represents structured organizational knowledge extracted from conversations, documents, events, applications, or AI reasoning.

## Attributes

- Memory ID
- Workspace ID
- Source
- Memory Type
- Title
- Description
- Content
- Metadata
- Created By
- Created Date
- Updated Date
- Status
- Lifecycle State
- Intelligence Scores
- Relationships

## Relationships

Memory may relate to:

- Tasks
- Goals
- Decisions
- Events
- Insights
- Documents
- People
- Projects
- Connectors

---

# 2.2 Workspace

Represents an isolated organizational environment.

## Attributes

- Workspace ID
- Name
- Owner
- Status
- Quota
- Active Users
- Connected Systems
- Policies

Relationships

Workspace owns:

- Memories
- Connectors
- Runtime Events
- Operators
- Policies

---

# 2.3 Connector

Represents an external integration.

Examples

- Slack

- Microsoft Teams

- Gmail

- Google Calendar

- CRM

- ERP

## Attributes

- Connector ID

- Type

- Status

- Authentication

- Health

- Last Sync

- Workspace

Relationships

Connector generates Events.

---

# 2.4 Event

Represents any runtime occurrence.

Examples

- Memory Created

- Slack Message

- User Login

- Connector Failure

- Runtime Warning

- Policy Trigger

Attributes

- Event ID

- Timestamp

- Source

- Severity

- Payload

- Workspace

Relationships

Events create or modify Memories.

---

# 2.5 Intelligence Profile

Every Memory owns exactly one Intelligence Profile.

Attributes

- Importance

- Confidence

- Freshness

- Priority

- Composite Score (MIS)

- Explainability Factors

Relationships

One-to-One with Memory.

---

# 2.6 Knowledge Node

Represents a node inside the enterprise knowledge graph.

Examples

- Person

- Project

- Decision

- Customer

- Product

- Risk

- Goal

Attributes

- Node ID

- Type

- Label

- Metadata

Relationships

Knowledge Nodes connect through Graph Relationships.

---

# 2.7 Operator

Represents an administrator of CGMS.

Attributes

- Operator ID

- Name

- Role

- Permissions

- Audit History

Relationships

Operators manage Workspaces and Runtime.

---

# 2.8 Policy

Represents governance logic.

Examples

- Retention Policy

- Quarantine Policy

- Commercial Policy

- Security Policy

- Workspace Policy

Policies react to Events.

---

# 2.9 Runtime Session

Represents one execution session.

Attributes

- Session ID

- Start Time

- End Time

- Health

- Runtime Metrics

- Connected Services

Relationships

Runtime Sessions generate Timeline Events.

---

# 2.10 Commercial Plan

Represents product licensing.

Attributes

- Plan

- Features

- Workspace Limits

- Connector Limits

- AI Limits

- Billing

Relationships

Commercial Plans govern Workspace capabilities.

---

# 3. Enterprise Knowledge Graph Specification

## Purpose

The Enterprise Knowledge Graph is the cognitive backbone of CGMS.

Rather than storing isolated memories, CGMS continuously builds an evolving graph of organizational knowledge.

Every memory, task, decision, event, project, document, connector, workspace and person becomes part of a connected enterprise knowledge network.

The graph enables contextual reasoning rather than simple keyword search.

---

# Design Objectives

The Knowledge Graph shall:

- connect organizational knowledge
- preserve conversational context
- support explainable AI reasoning
- enable semantic discovery
- improve memory retrieval
- support impact analysis
- identify hidden relationships
- provide organizational intelligence

---

# Graph Components

The graph consists of two elements:

## Nodes

Nodes represent entities.

## Edges

Edges represent relationships.

---

# Node Types

CGMS initially supports the following node classes.

### Memory

Represents stored organizational knowledge.

Examples

- Decision
- Goal
- Task
- Insight
- Event

---

### Person

Represents users and stakeholders.

Examples

- Murphy
- Sales Director
- Commercial Intelligence Manager

---

### Workspace

Represents organizational boundaries.

---

### Project

Examples

- CGMS v2
- Commercial Dashboard
- Export Strategy

---

### Decision

Examples

- Adopt Event Driven Architecture
- Introduce Memory Intelligence

---

### Task

Examples

- Build Knowledge Graph
- Implement Memory Scoring

---

### Goal

Examples

- Reach GA
- Publish Research Paper

---

### Connector

Examples

- Slack

- Gmail

- Teams

---

### Document

Examples

- ADR

- Research Paper

- Product Specification

---

### Event

Examples

- Memory Created

- Workspace Switched

- Connector Failure

---

### Policy

Examples

- Retention Policy

- Quarantine Policy

---

# Edge Types

Relationships provide meaning.

Examples include:

CREATED

REFERENCES

DEPENDS_ON

BELONGS_TO

GENERATED_BY

UPDATED_BY

SUPPORTS

IMPLEMENTS

SUPERSEDES

RELATED_TO

ASSIGNED_TO

APPROVED_BY

BLOCKED_BY

PART_OF

LINKED_TO

---

# Example Knowledge Graph

Murphy

│

├── created

│

▼

CGMS v2

│

├── contains

│

▼

Memory Intelligence

│

├── implements

│

▼

ADR-001

│

├── creates

│

▼

Decision

│

├── generates

│

▼

Runtime Event

│

└── updates

Memory

---

# Graph Characteristics

The graph is

- dynamic
- event-driven
- explainable
- versioned
- workspace aware
- tenant isolated
- queryable
- AI consumable

---

# Graph Queries

CGMS shall support questions such as

Show every decision related to Memory Intelligence.

Show tasks blocked by ADR-001.

Show every workspace using Slack.

Show all goals supported by Project CGMS.

Which memories are connected to Commercial Intelligence?

Which decisions have no implementation?

What changed after Runtime v1.70?

---

# Future Extensions

Future releases may include

- graph embeddings

- graph neural networks

- probabilistic relationships

- temporal graph reasoning

- causal inference

- predictive graph analytics

without redesigning the core graph architecture.

---

# 4. Enterprise Service Architecture

## Overview

CGMS is implemented as a modular service-oriented platform.

Each service owns one business capability and communicates through events and well-defined APIs.

No service directly owns another service's business rules.

---

# Service Catalogue

The following services constitute the initial CGMS service landscape.

## 4.1 Memory Service

Responsibilities

- Capture memories
- Update memories
- Archive memories
- Restore memories
- Search memories

Publishes Events

- MemoryCreated
- MemoryUpdated
- MemoryArchived

Consumes

- Connector Events
- Intelligence Requests

---

## 4.2 Intelligence Service

Responsibilities

- Importance scoring
- Confidence scoring
- Freshness calculation
- Priority calculation
- Explainability
- Memory ranking

Publishes

MemoryScored

Consumes

MemoryCreated

MemoryUpdated

MemoryReferenced

---

## 4.3 Knowledge Graph Service

Responsibilities

- Node creation
- Relationship creation
- Graph traversal
- Similarity discovery
- Impact analysis

Publishes

GraphUpdated

Consumes

MemoryScored

MemoryUpdated

DecisionCreated

---

## 4.4 Connector Service

Responsibilities

- Connector lifecycle
- Authentication
- Synchronisation
- Health monitoring
- Event normalisation

Publishes

ConnectorEventReceived

ConnectorFailure

ConnectorRecovered

---

## 4.5 Runtime Service

Responsibilities

- Event orchestration
- Runtime metrics
- Timeline
- Health
- Observability

Publishes

RuntimeEvent

RuntimeHealthChanged

---

## 4.6 Governance Service

Responsibilities

- Policies
- Quarantine
- Kill switch
- Compliance
- Audit

Publishes

PolicyTriggered

AuditRecorded

---

## 4.7 Workspace Service

Responsibilities

- Workspace lifecycle
- Quotas
- Isolation
- Metrics

Publishes

WorkspaceCreated

WorkspaceUpdated

WorkspaceSuspended

---

## 4.8 Operator Service

Responsibilities

- Dashboard
- Runtime controls
- Monitoring
- Runtime commands

Publishes

OperatorAction

Consumes

Runtime Events

---

## 4.9 Commercial Service

Responsibilities

- Plans
- Licensing
- Billing
- Usage

Publishes

PlanChanged

QuotaExceeded

---

## Service Communication

Services communicate through:

- REST APIs
- Domain Events

No service should depend on database tables owned by another service.

---

## Architectural Constraint

Business logic shall exist only within service boundaries.

Routes are orchestration points.

Repositories are persistence points.

Services own business behaviour.

---

# 5. Enterprise Event Taxonomy

## Overview

CGMS is an event-driven enterprise platform.

Every significant business occurrence is represented as a domain event.

Events are immutable.

Events are timestamped.

Events are auditable.

Events drive intelligence.

---

# Event Categories

CGMS defines the following event families.

---

## Memory Events

Examples

MemoryCaptured

MemoryValidated

MemoryUpdated

MemoryReferenced

MemoryArchived

MemoryDeleted

MemoryRestored

MemoryExpired

---

## Intelligence Events

MemoryScored

ImportanceCalculated

ConfidenceCalculated

PriorityCalculated

FreshnessCalculated

ScoreRecomputed

ExplainabilityGenerated

---

## Knowledge Graph Events

NodeCreated

NodeUpdated

RelationshipCreated

RelationshipRemoved

GraphRebuilt

GraphMerged

---

## Workspace Events

WorkspaceCreated

WorkspaceActivated

WorkspaceSuspended

WorkspaceDeleted

QuotaExceeded

WorkspaceSwitched

---

## Connector Events

ConnectorActivated

ConnectorDeactivated

ConnectorHealthChanged

ConnectorFailure

ConnectorRecovered

ConnectorAuthenticated

ExternalEventReceived

---

## Runtime Events

RuntimeStarted

RuntimeStopped

RuntimeRecovered

RuntimePaused

RuntimeResumed

HealthChanged

LatencyThresholdExceeded

---

## Operator Events

OperatorLogin

OperatorLogout

OperatorCommandIssued

DashboardOpened

RuntimeRefreshRequested

---

## Governance Events

PolicyTriggered

PolicyUpdated

AuditRecorded

QuarantineApplied

KillSwitchActivated

ComplianceViolationDetected

---

## Commercial Events

PlanAssigned

LicenseUpdated

UsageThresholdExceeded

SubscriptionRenewed

BillingCompleted

---

## AI Events

ReasoningStarted

ReasoningCompleted

RecommendationGenerated

RiskDetected

SummaryGenerated

KnowledgeSynthesized

---

# Event Metadata

Every event contains

Event ID

Timestamp

Workspace

Source

Category

Severity

Correlation ID

Payload

Version

---

# Event Principles

Events

- never change

- are append-only

- are replayable

- support auditing

- support debugging

- support AI reasoning

- support historical reconstruction

---

# 6. Cognitive Intelligence Pipeline

## Purpose

The Cognitive Intelligence Pipeline defines how CGMS transforms raw enterprise interactions into organizational intelligence.

Rather than simply storing information, the platform progressively enriches knowledge through multiple stages of cognitive processing.

Each stage increases the value of the information while preserving explainability.

---

# Cognitive Processing Flow

Conversation

↓

Context Detection

↓

Memory Extraction

↓

Memory Validation

↓

Memory Intelligence

↓

Knowledge Graph Update

↓

Semantic Reasoning

↓

Recommendation Generation

↓

Action Orchestration

↓

Continuous Learning

---

# Stage 1 — Context Detection

Objective

Understand the surrounding conversational context.

Outputs

- Participants
- Workspace
- Topic
- Time
- Related conversations
- Conversation intent
- Source application

---

# Stage 2 — Memory Extraction

Objective

Identify candidate memories.

Memory types include

- Decision

- Goal

- Task

- Insight

- Risk

- Event

- Commitment

- Question

- Constraint

---

# Stage 3 — Validation

Objective

Ensure extracted memories satisfy quality rules.

Validation includes

- duplicate detection

- completeness

- confidence threshold

- workspace policy

- required metadata

---

# Stage 4 — Memory Intelligence

Objective

Assign intelligence.

Produces

Importance

Confidence

Priority

Freshness

Composite Memory Intelligence Score

Explainability

---

# Stage 5 — Knowledge Graph Update

Objective

Connect memory with organizational knowledge.

Possible relationships

supports

blocks

implements

references

depends_on

created_by

assigned_to

related_to

---

# Stage 6 — Semantic Reasoning

Objective

Answer questions beyond keyword search.

Examples

Which decisions affect Project Alpha?

What risks have increased?

Which commitments remain open?

Which projects depend on this memory?

---

# Stage 7 — Recommendation Engine

Objective

Generate actionable guidance.

Examples

Suggested follow-up

Suggested archive

Suggested escalation

Suggested owner

Suggested related memories

Suggested project links

---

# Stage 8 — Action Orchestration

Objective

Convert intelligence into enterprise actions.

Examples

Notify operator

Create task

Update dashboard

Trigger connector

Generate report

Open incident

---

# Stage 9 — Continuous Learning

Objective

Improve platform behaviour over time.

Learning sources

User corrections

Operator feedback

Reference frequency

Duplicate resolution

Relationship validation

Workspace behaviour

---

# Explainability Requirement

Every pipeline stage shall expose

Input

Output

Decision

Confidence

Processing time

Responsible service

No stage shall produce an unexplainable result.

---

# Pipeline Principles

The Cognitive Intelligence Pipeline shall be

- event-driven

- deterministic where possible

- explainable

- modular

- auditable

- extensible

- workspace aware

- AI assisted

- continuously improving

---

# 7. Enterprise API Standards

## Purpose

The Enterprise API Standards define how every service inside CGMS exposes functionality.

The objective is consistency, discoverability, explainability, versioning, and long-term maintainability.

---

# API Principles

Every API shall be

- RESTful
- Versioned
- Stateless
- Secure
- Observable
- Explainable
- Backward compatible

---

# Naming Standards

Resources shall use plural nouns.

Examples

/api/v1/memories

/api/v1/workspaces

/api/v1/connectors

/api/v1/events

/api/v1/operators

Avoid verbs inside resource paths.

Correct

POST /api/v1/memories

Incorrect

POST /api/v1/createMemory

---

# Response Structure

Every successful response should follow a consistent envelope.

{
    "success": true,
    "timestamp": "...",
    "version": "...",
    "data": { }
}

Errors should return

{
    "success": false,
    "error": {
        "code": "...",
        "message": "...",
        "details": "..."
    }
}

---

# API Versioning

Major changes

v1

v2

v3

Minor additions shall preserve compatibility.

Deprecated endpoints remain supported for one major version unless otherwise approved.

---

# Pagination

Large collections shall support

page

pageSize

sort

filter

search

---

# Filtering

Filtering shall be supported using query parameters.

Examples

status=active

workspace=finance

memoryType=decision

priority=high

---

# Authentication

APIs shall support

Bearer Tokens

OAuth 2.0

API Keys (service integrations)

Future

Enterprise SSO

OpenID Connect

---

# Observability

Every request shall include

Request ID

Correlation ID

Workspace ID

Processing Time

API Version

These values support debugging and distributed tracing.

---

# Idempotency

Where appropriate, POST operations shall support idempotency keys to prevent duplicate processing.

---

# Documentation

Every endpoint shall include

Purpose

Inputs

Outputs

Validation rules

Error codes

Example requests

Example responses

Related domain events

Associated ADR

---

# API Quality Metrics

Track

Latency

Availability

Error rate

Success rate

Payload size

Consumer usage

These metrics feed the Operator Console and Executive Dashboard.