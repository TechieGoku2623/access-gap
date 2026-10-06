from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from access_gap.cli import app
from access_gap.county_view import county_payload, designed_side_by_side, movers_for_therapy
from access_gap.lineage import build
from access_gap.report import choropleth_html, write_report
from access_gap.slice_data import load_slice

runner = CliRunner()


def test_build_lineage_and_tests_pass() -> None:
    _con, report = build()
    assert report.all_passed
    assert report.row_counts["marts.access_index"] == 36
    assert any(t.name == "acs_never_imputed_to_zero" and t.passed for t in report.tests)


def test_best_case_has_interval_and_contributions() -> None:
    payload = county_payload(load_slice(), "06075", "zolgensma")
    elig = payload["eligible_pop"]
    assert isinstance(elig, dict)
    assert elig["low"] < elig["high"]
    assert payload["silent_point_estimate"] is False
    assert payload["imputed_acs_to_zero"] is False
    contribs = payload["contributions"]
    assert isinstance(contribs, dict)
    assert contribs["travel"]["contribution"] is not None
    assert contribs["medicaid"]["score"] == 1.0


def test_gilmer_not_imputed() -> None:
    payload = county_payload(load_slice(), "54021", "zolgensma")
    assert payload["insured_missing"] is True
    assert payload["insured_pct"] is None
    assert "insurance" in payload["missing_components"]
    contribs = payload["contributions"]
    assert isinstance(contribs, dict)
    assert contribs["insurance"]["weight"] is None


def test_side_by_side_roles() -> None:
    rows = designed_side_by_side(load_slice())
    assert [r["role"] for r in rows] == ["best_case", "distance_dominated", "coverage_gap"]
    assert rows[2]["medicaid_covered"] is False
    assert rows[1]["rural"] is True


def test_sensitivity_movers() -> None:
    payload = movers_for_therapy(load_slice(), "zolgensma")
    assert payload["n_counties"] == 12
    assert payload["movers"]
    assert float(payload["min_spearman"]) <= 1.0


def test_choropleth_marks_missing_acs(tmp_path: object) -> None:
    html = choropleth_html(therapy_id="zolgensma")
    assert "54021" in html
    assert "impute" in html.lower()
    assert "zero" in html.lower()
    dest = Path(str(tmp_path)) / "map.html"
    write_report(dest, therapy_id="zolgensma")
    assert dest.is_file()


def test_cli_demo_build() -> None:
    result = runner.invoke(app, ["demo-build"])
    assert result.exit_code == 0, result.stdout
    assert "staging" in result.stdout
    assert "PASS" in result.stdout


def test_cli_county_and_sensitivity() -> None:
    one = runner.invoke(app, ["county", "--fips", "06075", "--therapy", "zolgensma"])
    assert one.exit_code == 0, one.stdout
    assert "06075" in one.stdout
    assert "INTERVAL" in one.stdout
    side = runner.invoke(app, ["county", "--compare"])
    assert side.exit_code == 0, side.stdout
    assert "48105" in side.stdout
    assert "48201" in side.stdout
    sens = runner.invoke(app, ["sensitivity", "--therapy", "zolgensma"])
    assert sens.exit_code == 0, sens.stdout
    assert "Spearman" in sens.stdout


def test_cli_demo_and_report(tmp_path: object) -> None:
    dest = Path(str(tmp_path)) / "report.html"
    rep = runner.invoke(app, ["report", "--dest", str(dest), "--therapy", "zolgensma"])
    assert rep.exit_code == 0, rep.stdout
    assert dest.is_file()
    demo = runner.invoke(app, ["demo"])
    assert demo.exit_code == 0, demo.stdout
    assert "demo-build" in demo.stdout or "Lineage" in demo.stdout
