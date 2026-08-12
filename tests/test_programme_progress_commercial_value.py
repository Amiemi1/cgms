from __future__ import annotations

from app.services.programme_progress.commercial_value import (
    build_commercial_value_view,
)


def test_executive_value_model_contains_approved_completion_metrics() -> None:
    model = build_commercial_value_view()

    assert model["model"]["version"] == "1.0"
    assert model["completion"]["overall_percent"] == 44
    assert model["completion"]["product_readiness_percent"] == 23
    assert model["completion"]["pilot_readiness_percent"] == 29

    assert model["completion"]["inputs"] == {
        "implemented": 9,
        "in_progress": 19,
        "not_started": 10,
        "pilot_ready": 0,
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

    assert second["completion"]["overall_percent"] == 44


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
