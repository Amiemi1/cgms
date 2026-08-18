from __future__ import annotations

from app.services.programme_progress.commercial_value import (
    build_commercial_value_view,
)


def test_executive_value_model_contains_approved_completion_metrics() -> None:
    model = build_commercial_value_view()

    assert model["model"]["version"] == "1.0"
    assert model["completion"]["overall_percent"] == 45
    assert model["completion"]["product_readiness_percent"] == 25
    assert model["completion"]["pilot_readiness_percent"] == 32

    assert model["completion"]["inputs"] == {
        "implemented": 9,
        "in_progress": 18,
        "not_started": 10,
        "pilot_ready": 1,
        "production_ready": 0,
        "total_capabilities": 38,
    }


def test_executive_value_model_contains_approved_gate_curve() -> None:
    model = build_commercial_value_view()

    gates = {
        item["gate"]: item
        for item in model["value_gates"]
    }

    assert list(gates) == [
        "As-Is",
        "Pilot Ready",
        "Commercial Ready",
        "Enterprise Ready",
        "Scale Ready",
    ]

    assert gates["As-Is"]["base_usd_m"] == 1.5
    assert gates["Pilot Ready"]["base_usd_m"] == 3.0
    assert gates["Commercial Ready"]["base_usd_m"] == 8.0
    assert gates["Enterprise Ready"]["base_usd_m"] == 25.0
    assert gates["Scale Ready"]["base_usd_m"] == 80.0

    assert gates["As-Is"]["base_ngn_bn"] == 2.04
    assert gates["Scale Ready"]["base_ngn_bn"] == 108.80


def test_executive_value_model_preserves_estimate_classification() -> None:
    model = build_commercial_value_view()

    assert model["model"]["classification"] == (
        "Governed management planning estimate — "
        "not a formal investment valuation"
    )

    assert model["market_intelligence"]["benchmark_set"] == [
        "Glean",
        "Microsoft 365 Copilot",
        "Notion AI",
        "Slack AI / Enterprise",
    ]


def test_value_story_links_need_feature_benefit_and_value() -> None:
    model = build_commercial_value_view()

    story = model["value_story"]

    assert len(story) == 8

    for item in story:
        assert item["industry_need"]
        assert item["feature"]
        assert item["benefit"]
        assert item["value_mechanism"]

    assert any(
        "Institutional knowledge" in item["industry_need"]
        and "Persistent organizational memory" in item["feature"]
        and "knowledge-loss cost" in item["value_mechanism"]
        for item in story
    )

    assert any(
        "AI-supported decisions" in item["industry_need"]
        and "Explainability" in item["feature"]
        and "compliance risk" in item["value_mechanism"]
        for item in story
    )


def test_executive_value_model_returns_isolated_copies() -> None:
    first = build_commercial_value_view()
    first["completion"]["overall_percent"] = 99

    second = build_commercial_value_view()

    assert second["completion"]["overall_percent"] == 45


def test_market_comparison_is_explicit_and_product_by_product() -> None:
    model = build_commercial_value_view()

    comparison = model["competitor_comparison"]

    assert len(comparison) == 5

    required = {
        "dimension",
        "cgms",
        "glean",
        "microsoft_365_copilot",
        "notion_ai",
        "slack_ai",
    }

    for item in comparison:
        assert required == set(item)
        assert all(item[key] for key in required)

    connector_row = next(
        item
        for item in comparison
        if item["dimension"] == "Cross-system search and connectors"
    )

    assert "100+" in connector_row["glean"]
    assert "100+" in connector_row["microsoft_365_copilot"]
    assert "Permission-aware" in connector_row["notion_ai"]
    assert "Enterprise+" in connector_row["slack_ai"]


def test_value_curve_exposes_incremental_base_value_unlock() -> None:
    model = build_commercial_value_view()

    assert model["headline"]["scale_multiple_vs_as_is"] == 53.3

    gates = {
        item["gate"]: item
        for item in model["value_gates"]
    }

    assert gates["As-Is"]["incremental_base_usd_m"] == 0.0
    assert gates["Pilot Ready"]["incremental_base_usd_m"] == 1.5
    assert gates["Commercial Ready"]["incremental_base_usd_m"] == 5.0
    assert gates["Enterprise Ready"]["incremental_base_usd_m"] == 17.0
    assert gates["Scale Ready"]["incremental_base_usd_m"] == 55.0

    assert gates["Pilot Ready"]["unlock_label"] == (
        "Value unlocked +$1.5m"
    )
    assert gates["Scale Ready"]["unlock_label"] == (
        "Value unlocked +$55.0m"
    )


def test_value_curve_preserves_approved_base_values() -> None:
    model = build_commercial_value_view()

    gates = {
        item["gate"]: item["base_usd_m"]
        for item in model["value_gates"]
    }

    assert gates == {
        "As-Is": 1.5,
        "Pilot Ready": 3.0,
        "Commercial Ready": 8.0,
        "Enterprise Ready": 25.0,
        "Scale Ready": 80.0,
    }


def test_buyer_intelligence_uses_approved_scoring_model() -> None:
    model = build_commercial_value_view()

    buyer = model["buyer_intelligence"]

    assert buyer["version"] == "1.0"
    assert buyer["as_of"] == "13 August 2026"
    assert buyer["scoring_model"]["scale"] == 100

    dimensions = {
        item["dimension"]: item["weight_percent"]
        for item in buyer["scoring_model"]["dimensions"]
    }

    assert dimensions == {
        "Industry Need Intensity": 25,
        "Complementarity with Existing Stack": 25,
        "Digital / AI Maturity": 20,
        "Economic & Operational Scale": 20,
        "Commercial Accessibility / Partnership Propensity": 10,
    }

    assert sum(dimensions.values()) == 100


def test_buyer_intelligence_preserves_enterprise_and_platform_separation() -> None:
    model = build_commercial_value_view()

    buyer = model["buyer_intelligence"]

    enterprise = {
        item["organization"]: item
        for item in buyer["enterprise_clients"]
    }

    platform = {
        item["organization"]: item
        for item in buyer["strategic_platform_opportunities"]
    }

    assert set(enterprise) == {
        "MTN Group",
        "Standard Bank Group",
        "Access Bank",
        "NNPC Ltd",
        "Airtel Africa",
        "Dangote Cement",
    }

    assert set(platform) == {
        "ServiceNow",
        "Microsoft",
    }

    assert enterprise["MTN Group"]["strategic_fit_score"] == 95
    assert enterprise["Standard Bank Group"]["strategic_fit_score"] == 94
    assert enterprise["Access Bank"]["strategic_fit_score"] == 91
    assert enterprise["NNPC Ltd"]["strategic_fit_score"] == 90
    assert enterprise["Airtel Africa"]["strategic_fit_score"] == 86
    assert enterprise["Dangote Cement"]["strategic_fit_score"] == 83

    assert platform["ServiceNow"]["strategic_fit_score"] == 91
    assert platform["Microsoft"]["strategic_fit_score"] == 87


def test_buyer_intelligence_accounts_have_required_governed_fields() -> None:
    model = build_commercial_value_view()

    buyer = model["buyer_intelligence"]

    accounts = (
        buyer["enterprise_clients"]
        + buyer["strategic_platform_opportunities"]
    )

    required = {
        "organization",
        "opportunity_type",
        "best_entry_gate",
        "strategic_fit_score",
        "fit_band",
        "evidence_confidence",
        "evidence_as_of",
        "current_state",
        "strategic_gap_hypothesis",
        "cgms_fit",
        "initial_use_case",
        "evidence_basis",
        "score_components",
    }

    assert len(accounts) == 8

    for account in accounts:
        assert required == set(account)
        assert all(
            account[field]
            for field in required
        )
        assert 0 <= account["strategic_fit_score"] <= 100
        assert account["evidence_as_of"] == "13 August 2026"


def test_all_value_gates_expose_buyer_universe() -> None:
    model = build_commercial_value_view()

    gates = model["value_gates"]

    assert len(gates) == 5

    for gate in gates:
        assert gate["buyer_universe"]
        assert gate["illustrative_accounts"]

    assert gates[0]["buyer_universe"] == (
        "Design partners / structured discovery"
    )

    assert gates[-1]["buyer_universe"] == (
        "Platform distribution / OEM / strategic transaction"
    )


def test_buyer_intelligence_disclaimer_rejects_implied_customer_status() -> None:
    model = build_commercial_value_view()

    disclaimer = model["buyer_intelligence"]["disclaimer"]

    assert "does not imply customer status" in disclaimer
    assert "expressed interest" in disclaimer
    assert "acquisition intent" in disclaimer


def test_buyer_strategic_fit_scores_are_exact_weighted_calculations() -> None:
    model = build_commercial_value_view()

    buyer = model["buyer_intelligence"]

    weights = {
        item["dimension"]: item["weight_percent"]
        for item in buyer["scoring_model"]["dimensions"]
    }

    accounts = (
        buyer["enterprise_clients"]
        + buyer["strategic_platform_opportunities"]
    )

    for account in accounts:
        scores = {
            item["dimension"]: item["score"]
            for item in account["score_components"]
        }

        assert set(scores) == set(weights)

        weighted_numerator = sum(
            scores[dimension] * weights[dimension]
            for dimension in weights
        )

        assert weighted_numerator % 100 == 0

        calculated_score = (
            weighted_numerator // 100
        )

        assert calculated_score == account["strategic_fit_score"]


def test_buyer_score_components_are_complete_and_bounded() -> None:
    model = build_commercial_value_view()

    buyer = model["buyer_intelligence"]

    approved_dimensions = {
        item["dimension"]
        for item in buyer["scoring_model"]["dimensions"]
    }

    accounts = (
        buyer["enterprise_clients"]
        + buyer["strategic_platform_opportunities"]
    )

    for account in accounts:
        components = account["score_components"]

        assert len(components) == 5

        assert {
            item["dimension"]
            for item in components
        } == approved_dimensions

        assert {
            item["label"]
            for item in components
        } == {
            "Need",
            "Stack",
            "AI",
            "Scale",
            "Access",
        }

        assert all(
            0 <= item["score"] <= 100
            for item in components
        )


def test_approved_headline_fit_scores_remain_unchanged() -> None:
    model = build_commercial_value_view()

    buyer = model["buyer_intelligence"]

    scores = {
        item["organization"]: item["strategic_fit_score"]
        for item in (
            buyer["enterprise_clients"]
            + buyer["strategic_platform_opportunities"]
        )
    }

    assert scores == {
        "MTN Group": 95,
        "Standard Bank Group": 94,
        "Access Bank": 91,
        "NNPC Ltd": 90,
        "Airtel Africa": 86,
        "Dangote Cement": 83,
        "ServiceNow": 91,
        "Microsoft": 87,
    }
