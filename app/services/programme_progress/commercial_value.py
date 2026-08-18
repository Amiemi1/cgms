from __future__ import annotations

from copy import deepcopy
from typing import Any, Final


_OVERALL_COMPLETION_STATUS_WEIGHTS: Final[dict[str, float]] = {
    "not_started": 0.0,
    "in_progress": 0.50,
    "implemented": 0.80,
    "pilot_ready": 0.90,
    "production_ready": 1.00,
}


_EXECUTIVE_VALUE_MODEL: Final[dict[str, Any]] = {
    "model": {
        "name": "CGMS Executive Value Model",
        "version": "1.0",
        "as_of": "18 August 2026",
        "classification": (
            "Governed management planning estimate — "
            "not a formal investment valuation"
        ),
        "currency": {
            "primary": "USD",
            "secondary": "NGN",
            "usd_ngn_assumption": 1360,
            "fx_basis": (
                "Dated management assumption for dashboard translation; "
                "refresh separately from engineering-state changes"
            ),
        },
    },
    "completion": {
        "overall_percent": 45,
        "method": (
            "Weighted capability-completion index using the governed "
            "38-capability Product Readiness estate"
        ),
        "inputs": {
            "implemented": 9,
            "in_progress": 18,
            "not_started": 10,
            "pilot_ready": 1,
            "production_ready": 0,
            "total_capabilities": 38,
        },
        "weights": deepcopy(
            _OVERALL_COMPLETION_STATUS_WEIGHTS
        ),
        "product_readiness_percent": 25,
        "pilot_readiness_percent": 32,
        "interpretation": (
            "Overall Completion measures progress through the build-to-scale "
            "journey. Product Readiness and Pilot Readiness remain separate "
            "governed readiness measures and must not be conflated with it."
        ),
    },
    "headline": {
        "as_is_base_usd_m": 1.5,
        "as_is_base_ngn_bn": 2.04,
        "next_gate": "Pilot Ready",
        "next_gate_base_usd_m": 3.0,
        "next_gate_base_ngn_bn": 4.08,
        "confidence": "Medium",
        "value_curve_summary": (
            "Base indicative value expands from $1.5m As-Is to $80m "
            "at Scale Ready as technical, commercial and market risk "
            "is progressively retired."
        ),
        "scale_multiple_vs_as_is": 53.3,
    },
    "value_gates": [
        {
            "gate": "As-Is",
            "low_usd_m": 0.8,
            "base_usd_m": 1.5,
            "high_usd_m": 2.5,
            "low_ngn_bn": 1.088,
            "base_ngn_bn": 2.04,
            "high_ngn_bn": 3.40,
            "confidence": "Medium",
            "confidence_class": "medium",
            "unlock_label": "Current base",
            "incremental_base_usd_m": 0.0,
            "buyer_universe": (
                "Design partners / structured discovery"
            ),
            "illustrative_accounts": (
                "Access Bank · Dangote Cement"
            ),
            "basis": (
                "Replacement cost, architecture/IP, engineering evidence "
                "and current productization risk"
            ),
        },
        {
            "gate": "Pilot Ready",
            "low_usd_m": 1.5,
            "base_usd_m": 3.0,
            "high_usd_m": 5.0,
            "low_ngn_bn": 2.04,
            "base_ngn_bn": 4.08,
            "high_ngn_bn": 6.80,
            "confidence": "Low–Medium",
            "confidence_class": "low-medium",
            "unlock_label": "Value unlocked +$1.5m",
            "incremental_base_usd_m": 1.5,
            "buyer_universe": (
                "Paid enterprise pilots"
            ),
            "illustrative_accounts": (
                "MTN · Access Bank · NNPC · Dangote Cement"
            ),
            "basis": (
                "Paid-pilot evidence, enterprise validation and reduced "
                "technical/product adoption risk"
            ),
        },
        {
            "gate": "Commercial Ready",
            "low_usd_m": 4.0,
            "base_usd_m": 8.0,
            "high_usd_m": 14.0,
            "low_ngn_bn": 5.44,
            "base_ngn_bn": 10.88,
            "high_ngn_bn": 19.04,
            "confidence": "Low",
            "confidence_class": "low",
            "unlock_label": "Value unlocked +$5.0m",
            "incremental_base_usd_m": 5.0,
            "buyer_universe": (
                "Enterprise procurement"
            ),
            "illustrative_accounts": (
                "MTN · Standard Bank · Airtel Africa · Access Bank"
            ),
            "basis": (
                "Commercial packaging plus approximately $1.5m base-case "
                "credible ARR and retention evidence"
            ),
        },
        {
            "gate": "Enterprise Ready",
            "low_usd_m": 12.0,
            "base_usd_m": 25.0,
            "high_usd_m": 45.0,
            "low_ngn_bn": 16.32,
            "base_ngn_bn": 34.00,
            "high_ngn_bn": 61.20,
            "confidence": "Low",
            "confidence_class": "low",
            "unlock_label": "Value unlocked +$17.0m",
            "incremental_base_usd_m": 17.0,
            "buyer_universe": (
                "Regulated / multi-country enterprise deployment"
            ),
            "illustrative_accounts": (
                "Standard Bank · MTN · Airtel Africa · NNPC"
            ),
            "basis": (
                "Approximately $5m base-case ARR with enterprise security, "
                "reliability, integration and evidence gates satisfied"
            ),
        },
        {
            "gate": "Scale Ready",
            "low_usd_m": 40.0,
            "base_usd_m": 80.0,
            "high_usd_m": 150.0,
            "low_ngn_bn": 54.40,
            "base_ngn_bn": 108.80,
            "high_ngn_bn": 204.00,
            "confidence": "Scenario",
            "confidence_class": "scenario",
            "unlock_label": "Value unlocked +$55.0m",
            "incremental_base_usd_m": 55.0,
            "buyer_universe": (
                "Platform distribution / OEM / strategic transaction"
            ),
            "illustrative_accounts": (
                "ServiceNow · Microsoft"
            ),
            "basis": (
                "Approximately $15m base-case ARR plus validated growth, "
                "retention, distribution and scale economics"
            ),
        },
    ],
    "valuation_methodology": [
        {
            "component": "Replacement-cost / software-asset value",
            "description": (
                "Validated software estate, architecture, governance "
                "and equivalent rebuild effort"
            ),
        },
        {
            "component": "Risk-adjusted commercial value",
            "description": (
                "Commercial maturity, credible ARR, retention and "
                "enterprise-adoption evidence"
            ),
        },
        {
            "component": "Strategic / IP option value",
            "description": (
                "Organizational memory, explainability, event intelligence "
                "and IP differentiation"
            ),
        },
    ],
    "software_estate": {
        "tracked_files": 436,
        "application_python_files": 304,
        "application_python_lines": 35063,
        "test_python_files": 75,
        "test_python_lines": 19237,
        "html_template_lines": 22750,
        "service_domains": 40,
        "application_classes": 162,
        "application_functions": 744,
        "application_async_functions": 56,
        "executed_regression_tests": 651,
    },
    "value_story": [
        {
            "industry_need": (
                "Institutional knowledge is lost when experts leave, "
                "teams change or decisions are poorly documented."
            ),
            "feature": (
                "Persistent organizational memory and contextual capture"
            ),
            "benefit": (
                "Retains institutional context beyond individual people "
                "and isolated conversations."
            ),
            "value_mechanism": (
                "Reduces knowledge-loss cost, repeated discovery and "
                "rework while improving business continuity."
            ),
        },
        {
            "industry_need": (
                "Critical information is fragmented across applications, "
                "documents, messages and operational systems."
            ),
            "feature": (
                "Semantic search, contextual retrieval and enterprise "
                "connector architecture"
            ),
            "benefit": (
                "Surfaces relevant organizational context faster and "
                "across otherwise disconnected information sources."
            ),
            "value_mechanism": (
                "Improves knowledge-worker productivity, shortens search "
                "time and increases reuse of existing organizational knowledge."
            ),
        },
        {
            "industry_need": (
                "Organizations struggle to identify which signals, events "
                "and historical context require action."
            ),
            "feature": (
                "Memory Intelligence, event intelligence and insight scoring"
            ),
            "benefit": (
                "Prioritizes what matters and connects current events with "
                "relevant historical organizational context."
            ),
            "value_mechanism": (
                "Improves decision speed, earlier risk detection and "
                "opportunity identification."
            ),
        },
        {
            "industry_need": (
                "AI-supported decisions can lack traceability, explainability "
                "and defensible evidence."
            ),
            "feature": (
                "Explainability, lineage, persistent audit and governance"
            ),
            "benefit": (
                "Creates traceable reasoning, evidence and accountable "
                "organizational memory."
            ),
            "value_mechanism": (
                "Reduces governance and compliance risk while increasing "
                "trust in AI-assisted decision processes."
            ),
        },
        {
            "industry_need": (
                "Enterprise adoption requires strong access control, "
                "tenant separation and auditable security."
            ),
            "feature": (
                "Secure authentication, RBAC, workspace isolation and "
                "persistent audit controls"
            ),
            "benefit": (
                "Separates organizational contexts and governs who can "
                "access or act on information."
            ),
            "value_mechanism": (
                "Improves enterprise deployment confidence and expands "
                "the addressable regulated-enterprise use case."
            ),
        },
        {
            "industry_need": (
                "Decisions often become disconnected from goals, tasks, "
                "events and subsequent execution."
            ),
            "feature": (
                "Goals, tasks, timeline, orchestration and event-driven "
                "execution context"
            ),
            "benefit": (
                "Preserves the connection between why a decision was made "
                "and what action followed."
            ),
            "value_mechanism": (
                "Strengthens execution continuity, accountability and "
                "cross-team coordination."
            ),
        },
        {
            "industry_need": (
                "Leaders have limited visibility into organizational-memory "
                "health, knowledge gaps and emerging context risk."
            ),
            "feature": (
                "Executive memory-health and programme intelligence dashboards"
            ),
            "benefit": (
                "Converts complex platform evidence into actionable "
                "management visibility."
            ),
            "value_mechanism": (
                "Supports faster executive intervention, investment "
                "prioritization and evidence-based governance."
            ),
        },
        {
            "industry_need": (
                "Organizations need AI infrastructure that can complement "
                "existing platforms rather than force complete replacement."
            ),
            "feature": (
                "Vendor-neutral cognitive memory and event-intelligence layer"
            ),
            "benefit": (
                "Provides a persistent context layer across enterprise tools "
                "and workflows."
            ),
            "value_mechanism": (
                "Reduces platform-displacement friction and creates a broader "
                "integration-led commercialization pathway."
            ),
        },
    ],
    "market_position": [
        {
            "dimension": "Persistent organizational memory",
            "cgms": "Potential differentiator",
            "market_context": (
                "CGMS is architected as a cross-system cognitive memory layer."
            ),
        },
        {
            "dimension": "Explainability and lineage",
            "cgms": "Potential differentiator",
            "market_context": (
                "Governed evidence and traceability are designed into "
                "the product architecture."
            ),
        },
        {
            "dimension": "Decision and event intelligence",
            "cgms": "Potential differentiator",
            "market_context": (
                "CGMS links memory, events, decisions and intelligent action."
            ),
        },
        {
            "dimension": "Enterprise search",
            "cgms": "In progress",
            "market_context": (
                "Mature market alternatives currently have stronger "
                "enterprise productization."
            ),
        },
        {
            "dimension": "Connector breadth",
            "cgms": "Material gap",
            "market_context": (
                "Connector depth and production hardening remain important "
                "commercial-readiness work."
            ),
        },
        {
            "dimension": "Product experience",
            "cgms": "Material gap",
            "market_context": (
                "Current governed Product Experience category score is 7%."
            ),
        },
        {
            "dimension": "Enterprise integrations",
            "cgms": "Material gap",
            "market_context": (
                "Current governed Integrations category score is 13%."
            ),
        },
        {
            "dimension": "Distribution and traction",
            "cgms": "Very early",
            "market_context": (
                "No commercial traction is assumed in Valuation Model v1.0."
            ),
        },
    ],
    "competitor_comparison": [
        {
            "dimension": "Core market position",
            "cgms": (
                "Enterprise cognitive memory and event-intelligence layer"
            ),
            "glean": (
                "Enterprise search, enterprise context and agentic Work AI"
            ),
            "microsoft_365_copilot": (
                "Microsoft 365 work-grounded Copilot, search and agents"
            ),
            "notion_ai": (
                "AI workspace with enterprise search and autonomous agents"
            ),
            "slack_ai": (
                "Collaboration hub with AI-powered enterprise search "
                "and agent/workflow capabilities"
            ),
        },
        {
            "dimension": "Cross-system search and connectors",
            "cgms": (
                "In progress; connector breadth remains a material gap"
            ),
            "glean": (
                "Enterprise search across 100+ tools"
            ),
            "microsoft_365_copilot": (
                "Microsoft 365 data plus 100+ prebuilt Copilot connectors"
            ),
            "notion_ai": (
                "Permission-aware enterprise search across Notion "
                "and connected work applications"
            ),
            "slack_ai": (
                "Enterprise+ search across Slack, connected third-party "
                "applications and custom sources"
            ),
        },
        {
            "dimension": "Permission-aware governance",
            "cgms": (
                "In progress; authentication, RBAC, workspace isolation "
                "and audit remain Product Readiness priorities"
            ),
            "glean": (
                "Source permissions are fetched and enforced in search"
            ),
            "microsoft_365_copilot": (
                "Enterprise search operates within Microsoft 365 "
                "tenant and access-control boundaries"
            ),
            "notion_ai": (
                "Enterprise Search and Agents follow workspace "
                "and connected-source permissions"
            ),
            "slack_ai": (
                "Enterprise search results respect the searching user's "
                "access permissions"
            ),
        },
        {
            "dimension": "Agentic workflows and action",
            "cgms": (
                "Agent, orchestration and execution foundations exist; "
                "commercial productization remains in progress"
            ),
            "glean": (
                "Agents reason, plan and act using enterprise context"
            ),
            "microsoft_365_copilot": (
                "Agents extend Copilot with organizational knowledge, "
                "tools and actions"
            ),
            "notion_ai": (
                "Custom Agents automate recurring work using triggers, "
                "workspace context and actions"
            ),
            "slack_ai": (
                "AI search, Slackbot, workflow automation and "
                "agent integrations operate in the collaboration surface"
            ),
        },
        {
            "dimension": "Primary knowledge and context surface",
            "cgms": (
                "Persistent cross-system organizational memory, events, "
                "decisions, goals and intelligence"
            ),
            "glean": (
                "Indexed enterprise knowledge and contextual search"
            ),
            "microsoft_365_copilot": (
                "Microsoft Graph, Microsoft 365 content and "
                "connector-ingested enterprise data"
            ),
            "notion_ai": (
                "Notion workspace knowledge plus connected applications"
            ),
            "slack_ai": (
                "Slack conversations, files and connected application data"
            ),
        },
    ],
    "buyer_intelligence": {
        "name": "CGMS Buyer Intelligence",
        "version": "1.0",
        "as_of": "13 August 2026",
        "classification": (
            "Management strategic-fit hypotheses based on public evidence; "
            "not customer, engagement or transaction evidence"
        ),
        "scoring_model": {
            "scale": 100,
            "dimensions": [
                {
                    "dimension": "Industry Need Intensity",
                    "weight_percent": 25,
                },
                {
                    "dimension": "Complementarity with Existing Stack",
                    "weight_percent": 25,
                },
                {
                    "dimension": "Digital / AI Maturity",
                    "weight_percent": 20,
                },
                {
                    "dimension": "Economic & Operational Scale",
                    "weight_percent": 20,
                },
                {
                    "dimension": (
                        "Commercial Accessibility / Partnership Propensity"
                    ),
                    "weight_percent": 10,
                },
            ],
            "principle": (
                "The score measures strategic fit and addressability, not "
                "purchase probability, customer intent or acquisition intent."
            ),
            "calculation": (
                "Strategic Fit Score = sum(component score × dimension "
                "weight). All component scores use a 0–100 scale."
            ),
        },
        "buyer_universe_by_gate": [
            {
                "gate": "As-Is",
                "universe": "Design partners / structured discovery",
                "accounts": [
                    "Access Bank",
                    "Dangote Cement",
                ],
            },
            {
                "gate": "Pilot Ready",
                "universe": "Paid enterprise pilots",
                "accounts": [
                    "MTN Group",
                    "Access Bank",
                    "NNPC Ltd",
                    "Dangote Cement",
                ],
            },
            {
                "gate": "Commercial Ready",
                "universe": "Enterprise procurement",
                "accounts": [
                    "MTN Group",
                    "Standard Bank Group",
                    "Airtel Africa",
                    "Access Bank",
                ],
            },
            {
                "gate": "Enterprise Ready",
                "universe": (
                    "Regulated / multi-country enterprise deployment"
                ),
                "accounts": [
                    "Standard Bank Group",
                    "MTN Group",
                    "Airtel Africa",
                    "NNPC Ltd",
                ],
            },
            {
                "gate": "Scale Ready",
                "universe": (
                    "Platform distribution / OEM / strategic transaction"
                ),
                "accounts": [
                    "ServiceNow",
                    "Microsoft",
                ],
            },
        ],
        "enterprise_clients": [
            {
                "organization": "MTN Group",
                "opportunity_type": "Enterprise Client",
                "best_entry_gate": "Pilot Ready",
                "strategic_fit_score": 95,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 98,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 92,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 98,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 99,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 81,
                    },
                ],
                "fit_band": "Very High",
                "evidence_confidence": "High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Large multi-market telecom estate with established AI "
                    "and Cloud Centres of Excellence, substantial internal "
                    "software engineering capability and high-volume "
                    "analytics / operational-AI infrastructure."
                ),
                "strategic_gap_hypothesis": (
                    "Durable organizational context can remain fragmented "
                    "across applications, analytics, teams, interventions "
                    "and historical decisions."
                ),
                "cgms_fit": (
                    "Persistent organizational memory, event intelligence, "
                    "decision lineage, explainability and contextual recall "
                    "across existing systems rather than replacement of them."
                ),
                "initial_use_case": (
                    "Reconstruct and retain the complete context surrounding "
                    "network or commercial interventions, decisions and "
                    "downstream outcomes."
                ),
                "evidence_basis": (
                    "Official MTN investor, Genova AI and Azure partnership "
                    "materials reviewed for the dated intelligence snapshot."
                ),
            },
            {
                "organization": "Standard Bank Group",
                "opportunity_type": "Enterprise Client",
                "best_entry_gate": "Commercial Ready",
                "strategic_fit_score": 94,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 97,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 93,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 95,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 98,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 79,
                    },
                ],
                "fit_band": "Very High",
                "evidence_confidence": "High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Large regulated African banking group with substantial "
                    "multi-country scale and a strategy in which technology "
                    "and AI are foundational capabilities."
                ),
                "strategic_gap_hypothesis": (
                    "Cross-country institutional context, governance evidence "
                    "and decision history can be difficult to preserve and "
                    "retrieve consistently across complex regulated estates."
                ),
                "cgms_fit": (
                    "Governed institutional memory, regulated decision "
                    "lineage, contextual retrieval and multi-entity knowledge "
                    "continuity."
                ),
                "initial_use_case": (
                    "Preserve strategic and governance decision context across "
                    "multi-country transformation programmes."
                ),
                "evidence_basis": (
                    "Official Standard Bank investor and strategy materials "
                    "reviewed for the dated intelligence snapshot."
                ),
            },
            {
                "organization": "Access Bank",
                "opportunity_type": "Enterprise Client / Design Partner",
                "best_entry_gate": "Pilot Ready",
                "strategic_fit_score": 91,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 94,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 92,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 93,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 88,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 83,
                    },
                ],
                "fit_band": "Very High",
                "evidence_confidence": "High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Digital-capability and partnership orientation combining "
                    "digital platforms, data analytics, AI and technology "
                    "co-innovation."
                ),
                "strategic_gap_hypothesis": (
                    "Strategic initiatives and cross-functional digital "
                    "programmes can lose decision context, institutional "
                    "knowledge and traceability over time."
                ),
                "cgms_fit": (
                    "Governed memory, decision traceability, cross-functional "
                    "context and explainable institutional intelligence."
                ),
                "initial_use_case": (
                    "Controlled institutional-memory pilot around strategic "
                    "initiatives, governance decisions or digital programmes."
                ),
                "evidence_basis": (
                    "Official Access Bank Partnerships & Digital Capabilities "
                    "materials reviewed for the dated intelligence snapshot."
                ),
            },
            {
                "organization": "NNPC Ltd",
                "opportunity_type": "Enterprise Client",
                "best_entry_gate": "Pilot Ready",
                "strategic_fit_score": 90,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 96,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 90,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 82,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 99,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 73,
                    },
                ],
                "fit_band": "Very High",
                "evidence_confidence": "High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Large integrated energy organisation managing complex "
                    "operational, technical and investment programmes while "
                    "publicly advancing integrated data, AI and engineering "
                    "modernisation."
                ),
                "strategic_gap_hypothesis": (
                    "Long-duration programmes and operational decisions can "
                    "lose assumptions, stakeholder context, technical history "
                    "and lessons across teams and time."
                ),
                "cgms_fit": (
                    "Operational and programme memory, technical knowledge "
                    "continuity, event lineage and governance evidence."
                ),
                "initial_use_case": (
                    "Create persistent context around a bounded strategic "
                    "programme, major operational event or technical decision "
                    "chain."
                ),
                "evidence_basis": (
                    "Official NNPC financial, research, innovation and AI "
                    "materials reviewed for the dated intelligence snapshot."
                ),
            },
            {
                "organization": "Airtel Africa",
                "opportunity_type": "Enterprise Client",
                "best_entry_gate": "Commercial Ready",
                "strategic_fit_score": 86,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 90,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 84,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 87,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 95,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 61,
                    },
                ],
                "fit_band": "High",
                "evidence_confidence": "Medium–High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Large multi-market telecom and digital-services estate "
                    "with extensive mobile, data, mobile-money, fibre, data "
                    "centre and network-modernisation activity."
                ),
                "strategic_gap_hypothesis": (
                    "Cross-market decisions, network context and operational "
                    "learning can remain distributed across markets, teams "
                    "and technology surfaces."
                ),
                "cgms_fit": (
                    "Cross-market contextual intelligence, operational memory "
                    "and durable decision/event lineage."
                ),
                "initial_use_case": (
                    "Preserve and retrieve context around network, customer or "
                    "commercial interventions across multiple operating markets."
                ),
                "evidence_basis": (
                    "Official Airtel Africa corporate, operating and strategy "
                    "materials reviewed for the dated intelligence snapshot."
                ),
            },
            {
                "organization": "Dangote Cement",
                "opportunity_type": "Enterprise Client / Design Partner",
                "best_entry_gate": "Pilot Ready",
                "strategic_fit_score": 83,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 90,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 86,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 75,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 92,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 56,
                    },
                ],
                "fit_band": "High",
                "evidence_confidence": "Medium–High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Large multi-country industrial and logistics estate with "
                    "increasing use of AI-driven monitoring, automated "
                    "inspection and transport telematics."
                ),
                "strategic_gap_hypothesis": (
                    "Operational incidents, safety learning, plant knowledge "
                    "and logistics decisions can become fragmented across "
                    "sites, shifts and operating teams."
                ),
                "cgms_fit": (
                    "Operational-event memory, safety and incident lineage, "
                    "cross-plant knowledge retention and contextual learning."
                ),
                "initial_use_case": (
                    "Bounded operational-memory pilot around fleet safety, "
                    "plant incidents or recurring operational interventions."
                ),
                "evidence_basis": (
                    "Official Dangote Cement operations and AI-telematics "
                    "materials reviewed for the dated intelligence snapshot."
                ),
            },
        ],
        "strategic_platform_opportunities": [
            {
                "organization": "ServiceNow",
                "opportunity_type": "Strategic Platform Partner",
                "best_entry_gate": "Enterprise / Scale Ready",
                "strategic_fit_score": 91,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 92,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 88,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 98,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 97,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 70,
                    },
                ],
                "fit_band": "Very High Adjacency",
                "evidence_confidence": "High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Enterprise workflow and AI platform with Enterprise "
                    "Graph, AI governance / orchestration capabilities and a "
                    "large partner ecosystem for apps, agents and connectors."
                ),
                "strategic_gap_hypothesis": (
                    "Workflow and graph context do not eliminate the distinct "
                    "need for durable longitudinal organizational memory, "
                    "event history and decision lineage across systems."
                ),
                "cgms_fit": (
                    "Differentiated persistent memory and event-intelligence "
                    "extension that could complement workflow orchestration."
                ),
                "initial_use_case": (
                    "Integration or partner-built memory capability connecting "
                    "ServiceNow workflows with durable organizational context."
                ),
                "evidence_basis": (
                    "Official ServiceNow Enterprise Graph and partner-programme "
                    "materials reviewed for the dated intelligence snapshot."
                ),
            },
            {
                "organization": "Microsoft",
                "opportunity_type": (
                    "Strategic Platform / Distribution Partner"
                ),
                "best_entry_gate": "Enterprise / Scale Ready",
                "strategic_fit_score": 87,
                "score_components": [
                    {
                        "dimension": "Industry Need Intensity",
                        "label": "Need",
                        "score": 90,
                    },
                    {
                        "dimension": "Complementarity with Existing Stack",
                        "label": "Stack",
                        "score": 74,
                    },
                    {
                        "dimension": "Digital / AI Maturity",
                        "label": "AI",
                        "score": 100,
                    },
                    {
                        "dimension": "Economic & Operational Scale",
                        "label": "Scale",
                        "score": 100,
                    },
                    {
                        "dimension": (
                            "Commercial Accessibility / Partnership Propensity"
                        ),
                        "label": "Access",
                        "score": 60,
                    },
                ],
                "fit_band": "High Adjacency",
                "evidence_confidence": "High",
                "evidence_as_of": "13 August 2026",
                "current_state": (
                    "Large enterprise AI and productivity ecosystem built "
                    "around Microsoft Graph, Copilot, agents, connectors, "
                    "Azure and partner / marketplace distribution."
                ),
                "strategic_gap_hypothesis": (
                    "Broad search, graph and agent capabilities create overlap, "
                    "but durable cross-system organizational memory and "
                    "longitudinal event/decision lineage remain a distinct "
                    "architectural proposition."
                ),
                "cgms_fit": (
                    "Connector, Marketplace, co-sell or platform integration "
                    "path for a vendor-neutral cognitive-memory and "
                    "event-intelligence layer."
                ),
                "initial_use_case": (
                    "Package CGMS as an enterprise memory / event-intelligence "
                    "integration that complements Microsoft AI and data estates."
                ),
                "evidence_basis": (
                    "Official Microsoft Copilot connector, Graph, agent and "
                    "partner-distribution materials reviewed for the dated "
                    "intelligence snapshot."
                ),
            },
        ],
        "disclaimer": (
            "Named organizations are potential-client or strategic-fit "
            "hypotheses based solely on public information. Inclusion does "
            "not imply customer status, engagement, expressed interest, "
            "partnership discussions or acquisition intent."
        ),
    },

    "value_drivers": [
        "Persistent organizational-memory architecture",
        "40-service-domain software estate",
        "651-test validated regression surface",
        "Memory Intelligence and event-intelligence capability",
        "Explainability, governance and audit architecture",
        "Vendor-neutral cognitive-layer positioning",
        "Patent and IP evidence programme",
    ],
    "value_risks": [
        "Four unresolved P0 Product Readiness blockers",
        "One pilot-ready capability",
        "Zero production-ready capabilities",
        "Product Experience category score of 7%",
        "Integrations category score of 13%",
        "Backup and Restore not started",
        "No commercial traction assumed in the current valuation",
    ],
    "market_intelligence": {
        "as_of": "12 August 2026",
        "benchmark_set": [
            "Glean",
            "Microsoft 365 Copilot",
            "Notion AI",
            "Slack AI / Enterprise",
        ],
        "principle": (
            "Market benchmarks establish category context and commercial "
            "reference points; they are not direct CGMS valuation multiples."
        ),
        "source_register": [
            {
                "product": "Glean",
                "source": (
                    "Official Glean Enterprise Search and connector "
                    "documentation"
                ),
            },
            {
                "product": "Microsoft 365 Copilot",
                "source": (
                    "Official Microsoft Learn Copilot Search, connector "
                    "and agent documentation"
                ),
            },
            {
                "product": "Notion AI",
                "source": (
                    "Official Notion Enterprise Search and Custom Agent "
                    "documentation"
                ),
            },
            {
                "product": "Slack AI / Enterprise",
                "source": (
                    "Official Slack Enterprise Search and AI documentation"
                ),
            },
        ],
    },
}


def build_commercial_value_view() -> dict[str, Any]:
    """Return an isolated copy of the governed executive value model."""

    return deepcopy(
        _EXECUTIVE_VALUE_MODEL
    )
