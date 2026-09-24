"""Offline dashboard presentation contracts: no app startup or database access.

Also runnable directly with Python, outside pytest/conftest, during guarded apply.
CGMS_UI_TEST_ROOT may point to a disposable candidate tree for pre-write validation.
"""
from __future__ import annotations

import copy
import os
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from jinja2 import Environment, StrictUndefined, select_autoescape

ROOT = Path(os.environ.get("CGMS_UI_TEST_ROOT", Path(__file__).resolve().parents[1]))
TEMPLATES = ROOT / "app" / "dashboard" / "templates"


def programme_fixture() -> dict:
    """Representative presentation inputs, not a readiness-engine replacement."""
    return {
        "page": {
            "title": "CGMS Programme Progress Dashboard",
            "subtitle": "Governed delivery evidence",
            "current_sprint": "Sprint 22",
            "current_work": "CAP-005 Published / Post-Publication Governance Currency",
            "as_of": "23 September 2026",
            "branch": "cgms-v2-roadmap",
            "status": "CAP-005 engineering published; commercial pilot NOT READY",
            "canonical_record": "docs/CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md",
        },
        "summary": [
            {"label": "Current milestone", "value": "CAP-005 Published", "detail": "PILOT_READY; P0 retained"},
            {"label": "Current regression suite", "value": "739 passed", "detail": "Run #46 engineering evidence"},
            {"label": "Step 264R technical validation", "value": "696 + PostgreSQL PASS", "detail": "Historical Step 264R"},
            {"label": "Latest published checkpoint", "value": "9c683d2", "detail": "Recorded engineering publication"},
            {"label": "GitHub Actions", "value": "Run #46 — Success", "detail": "Engineering CI"},
            {"label": "Runtime contracts", "value": "PASS", "detail": "Recorded route uniqueness check"},
            {"label": "Pilot readiness", "value": "NOT READY", "detail": "Separate catalogue and P1 gaps remain"},
        ],
        "executive_value": {
            "completion": {"overall_percent": 48, "product_readiness_percent": 30, "pilot_readiness_percent": 39},
            "headline": {"as_is_base_usd_m": 1.5, "as_is_base_ngn_bn": 2.04,
                         "next_gate": "Pilot Ready", "next_gate_base_usd_m": 3.0,
                         "next_gate_base_ngn_bn": 4.08, "confidence": "Medium",
                         "value_curve_summary": "Planning assumption, not a valuation opinion",
                         "scale_multiple_vs_as_is": 53.3},
            "value_gates": [],
            "value_drivers": ["651-test validated regression surface", "Preserved value driver"],
            "value_risks": ["Two unresolved P0 Product Readiness blockers"],
            "valuation_methodology": [], "value_story": [],
            "buyer_intelligence": {"buyer_universe_by_gate": [], "scoring_model": {"dimensions": []},
                                   "enterprise_clients": [], "strategic_platform_opportunities": [],
                                   "disclaimer": "Named accounts are hypotheses, not confirmed customers."},
            "market_position": [], "competitor_comparison": [],
            "market_intelligence": {"as_of": "12 August 2026", "benchmark_set": [],
                                    "principle": "Dated market snapshot, not a current valuation"},
            "model": {"currency": {"usd_ngn_assumption": 1360}, "classification": "Management planning estimate"},
        },
        "foundations": [{"title": "Memory Engine", "status": "Complete"}],
        "current_focus": ["CAP-005 remains P0 and PILOT_READY"],
        "upcoming": ["Remaining P1 commercial blockers remain separately governed"],
        "sprints": [{"title": "Sprint 22", "status": "Complete — published", "status_class": "complete",
                     "summary": "Historical delivery", "milestones": [{"id": "PWI-001-187F",
                     "title": "Cross-workspace closure", "status": "Complete and published", "status_class": "complete"}]}],
        "navigation": [{"title": "Product Readiness", "path": "/product-readiness/dashboard",
                        "local_url": "https://127.0.0.1:8443/product-readiness/dashboard",
                        "description": "Existing interface", "access": "Existing authorization"}],
        "related_tools": [],
        "startup": [{"title": "Reference database startup", "purpose": "Existing command register",
                     "command": "docker compose up -d db"}],
        "validation": [
            {"title": "CAP-005 real PostgreSQL recovery validation", "result": "PASS — real backup/restore", "detail": "Preserved encrypted recovery evidence"},
            {"title": "Current full regression suite", "result": "536 passed", "detail": "PRG-001 complete regression"},
            {"title": "PWI-001 Step 187F integrated technical closure", "result": "PASS — publication pending", "detail": "679 passed at the pre-publication checkpoint"},
        ],
        "commits": [{"hash": "9c683d2", "title": "Recorded engineering commit", "status": "Published"}],
        "technical_debt": [{"title": "Recorded technical debt", "detail": "Historical statement retained"}],
        "governance": {"rule": "Engineering Governance Rule EG-001", "classification": "CAP-005 reconciliation",
                       "scope": "Recorded governed scope", "boundaries": "No unrelated mutation",
                       "canonical_record": "docs/CGMS_MASTER_CONTINUATION_PROMPT_v2.0.md"},
    }


class Tags(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict]] = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def by_id(self, item_id):
        return [(tag, attrs) for tag, attrs in self.tags if attrs.get("id") == item_id]


def rendered_programme(data=None):
    source = (TEMPLATES / "programme_progress_dashboard.html").read_text(encoding="utf-8-sig")
    env = Environment(autoescape=select_autoescape(default=True), undefined=StrictUndefined)
    return env.from_string(source).render(dashboard=data or programme_fixture(), principal={"role": "viewer"})


class DashboardUsabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = (TEMPLATES / "product_readiness_dashboard.html").read_text(encoding="utf-8-sig")
        cls.programme = (TEMPLATES / "programme_progress_dashboard.html").read_text(encoding="utf-8-sig")
        cls.rendered = rendered_programme()

    def test_programme_renders_without_application_import(self):
        self.assertIn("CGMS Programme Progress Dashboard", self.rendered)
        self.assertNotIn("{{", self.rendered)

    def test_render_does_not_mutate_input_metrics(self):
        fixture = programme_fixture()
        before = copy.deepcopy(fixture)
        rendered_programme(fixture)
        self.assertEqual(fixture, before)

    def test_main_overview_has_four_cards(self):
        match = re.search(r'<section class="summary-grid ui-overview".*?</section>', self.rendered, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(match[0].count('<article class="card">'), 4)
        for text in ("48%", "30%", "39%", "CAP-005 Published"):
            self.assertIn(text, match[0])

    def test_pilot_verdict_and_next_priorities_remain_visible(self):
        self.assertIn('class="ui-verdict"', self.rendered)
        self.assertIn("NOT READY", self.rendered)
        self.assertIn("Next priorities", self.rendered)

    def test_detail_sections_are_native_and_collapsed(self):
        tags = Tags(self.rendered)
        ids = ("engineering-evidence", "executive-value", "value-story", "strategic-position",
               "roadmap", "dashboards", "startup", "validation", "debt", "governance")
        for item_id in ids:
            found = tags.by_id("panel-" + item_id)
            self.assertEqual(len(found), 1, item_id)
            self.assertEqual(found[0][0], "details", item_id)
            self.assertNotIn("open", found[0][1], item_id)

    def test_historical_evidence_is_retained_and_labelled(self):
        for text in ("696 + PostgreSQL PASS", "536 passed", "679 passed", "651-test validated regression surface",
                     "Historical CI recovery baseline", "PRG-001 historical full regression suite",
                     "pre-publication validation snapshot", "PASS — publication pending"):
            self.assertIn(text, self.rendered)
        self.assertNotIn("<h3>Current full regression suite</h3>", self.rendered)

    def test_publication_snapshots_have_distinct_commit_scope(self):
        for text in ("9c683d277f46eb2c6012759c3ff45e0221e84763", "31a6265ae3d8d3d36c9425b482d62d2f466ab625",
                     "Run #46", "Run #47", "739 passed", "740 passed", "not a live GitHub poll",
                     "not this subsequent UI update"):
            self.assertIn(text, self.rendered)
        self.assertIn('class="hash-disclosure"', self.rendered)
        self.assertNotIn("Latest published checkpoint", self.rendered)

    def test_buyer_snapshot_and_disclaimers_survive(self):
        self.assertIn('id="buyer-opportunity"', self.rendered)
        self.assertIn("not confirmed customers", self.rendered)
        self.assertIn("12 August 2026", self.rendered)
        self.assertIn("1360", self.rendered)

    def test_startup_note_does_not_supply_a_secret(self):
        self.assertIn("CGMS_JWT_SECRET", self.rendered)
        self.assertIn("at least 32 characters", self.rendered)
        self.assertIn("temporary process-only", self.rendered.lower())
        self.assertIn("docker compose up -d db", self.rendered)
        self.assertNotIn("secrets.token_hex", self.rendered)

    def test_programme_autoescapes_untrusted_values(self):
        data = programme_fixture()
        data["upcoming"] = ['<img src=x onerror="alert(1)">']
        html = rendered_programme(data)
        self.assertIn("&lt;img", html)
        self.assertNotIn('<img src=x', html)

    def test_all_element_ids_are_unique(self):
        for source in (self.product, self.rendered):
            ids = [attrs["id"] for _, attrs in Tags(source).tags if "id" in attrs]
            self.assertEqual(len(ids), len(set(ids)))

    def test_product_filters_have_associated_labels(self):
        tags = Tags(self.product)
        labels = {attrs.get("for") for tag, attrs in tags.tags if tag == "label"}
        for item_id in ("capabilitySearch", "capabilityPriority", "capabilityStatus", "capabilityPageSize",
                        "recommendationSearch", "recommendationPriority", "recommendationPageSize"):
            self.assertEqual(len(tags.by_id(item_id)), 1)
            self.assertIn(item_id, labels)

    def test_existing_product_api_paths_are_unchanged(self):
        urls = re.findall(r'fetchJson\("([^"]+)"\)', self.product)
        self.assertEqual(urls, ["/product-readiness/assessment", "/product-readiness/capabilities",
                               "/product-readiness/recommendations", "/product-readiness/categories"])
        self.assertNotIn("window.fetch =", self.product)

    def test_summary_uses_full_datasets_and_distinct_pilot_count(self):
        block = self.product.split("function renderSummary(", 1)[1].split("function renderCategories", 1)[0]
        self.assertIn("capabilities.length", block)
        self.assertIn("recommendations.length", block)
        self.assertNotIn("filteredCapabilities", block)
        self.assertNotIn("filteredRecommendations", block)
        self.assertIn('"pilot_ready"', block)
        self.assertIn("Production-Ready Capabilities", self.product)

    def test_html_escaping_is_not_removed(self):
        self.assertIn("function escapeHtml(value)", self.product)
        self.assertIn("escapeHtml(name)", self.product)
        self.assertIn("escapeHtml(body)", self.product)
        self.assertIn("recommendation.reason", self.product)
        self.assertIn("new Option(format(value), value)", self.product)

    def test_navigation_print_and_empty_result_controls_exist(self):
        self.assertNotIn("<script", self.programme.lower())
        self.assertIn("details::details-content", self.programme)
        self.assertIn('href="#buyer-opportunity"', self.programme)
        for text in ("beforeprint", "afterprint", "No matching capabilities", "No matching recommendations",
                     "clearCapabilityFilters", "clearRecommendationFilters", 'aria-live="polite"'):
            self.assertIn(text, self.product)

    def test_empty_input_collections_still_render_programme(self):
        data = programme_fixture()
        for key in ("summary", "upcoming", "validation", "sprints", "commits", "startup", "navigation"):
            data[key] = []
        html = rendered_programme(data)
        self.assertIn("Current readiness overview", html)
        self.assertIn("Engineering Governance", html)

    def test_temporal_claims_are_not_promoted_to_live_checks(self):
        self.assertNotIn("fetch(", self.programme)
        self.assertIn("not a live GitHub poll", self.rendered)
        self.assertIn("Recorded items; not a fresh technical reassessment", self.rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
