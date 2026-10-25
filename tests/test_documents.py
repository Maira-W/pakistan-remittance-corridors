"""The documents and the dashboard are generated, so they can be tested like code."""

import json
import re

import pytest

from remit import config, dashboard, docs

DOCUMENTS = list(docs.OUTPUTS.values())


def text_of(path):
    return path.read_text(encoding="utf-8")


def test_committed_documents_are_what_the_templates_and_data_produce():
    for path, expected in docs.render_all().items():
        assert text_of(path) == expected, f"{path.name} is out of date: run `python -m remit report`"


def test_every_template_is_used_and_every_value_exists():
    assert {p.name for p in docs.TEMPLATE_DIR.glob("*.md")} == set(docs.OUTPUTS)
    values = docs.context()
    for template in docs.TEMPLATE_DIR.glob("*.md"):
        for name, _ in docs.PLACEHOLDER.findall(template.read_text(encoding="utf-8")):
            assert name in values, f"{template.name} uses {name}"


def test_a_missing_value_is_an_error_not_a_blank():
    with pytest.raises(KeyError):
        docs.render("{{no_such_value}}", {})
    assert docs.render("{{x:.1f}} points", {"x": 2.345}) == "2.3 points"


def test_no_leftover_placeholders_or_nan():
    for path in DOCUMENTS:
        text = text_of(path)
        assert "{{" not in text and "}}" not in text, path.name
        assert not re.search(r"\bnan\b|\bNaN\b|\binf\b", text), path.name


def test_relative_links_and_images_resolve():
    link = re.compile(r'(?:\]\(|src=")([^)"#\s]+)')
    for path in DOCUMENTS:
        for target in link.findall(text_of(path)):
            if re.match(r"[a-z]+:", target):
                continue
            assert (path.parent / target).exists(), f"{path.name} links to missing {target}"


def test_the_readme_headline_numbers_come_from_the_results(summary):
    readme = text_of(config.ROOT / "README.md")
    assert f"${summary['fy_totals_usd_m']['FY26'] / 1000:.1f} billion" in readme
    assert f"{summary['tier1_share_fy26_pct']:.0f}%" in readme


def test_no_document_overstates_the_eid_result(summary):
    """The pre-Eid lift is borderline for the total; the text must say so wherever it quotes it."""
    assert summary["eid"]["pooled"]["before_eid"]["p"] > 0.05
    for name in ("README.md", "docs/recommendation_memo.md"):
        text = text_of(config.ROOT / name).lower()
        assert "borderline" in text or "suggestive" in text or "uncertain" in text, name


def test_dashboard_is_current_and_its_data_are_valid_json():
    page = text_of(config.DASHBOARD / "dashboard.html")
    assert page == dashboard.render()
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1))
    assert {"summary", "perDay", "months", "stats", "calendar"} <= set(data)
    assert len(data["months"]) == 58 and "NaN" not in page
    assert all(len(v) == 58 for v in data["perDay"].values())


def test_figures_exist_and_are_not_empty():
    names = re.findall(r"docs/figures/([\w.]+\.png)", text_of(config.ROOT / "README.md"))
    assert names
    for name in names:
        assert (config.FIGURES / name).stat().st_size > 10_000
    assert len(list(config.FIGURES.glob("*.png"))) == 7
