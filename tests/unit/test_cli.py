from __future__ import annotations

from typer.testing import CliRunner

from access_gap.cli import app

runner = CliRunner()


def test_demo_plan_lists_five_designed_paths() -> None:
    result = runner.invoke(app, ["demo-plan", "--dry-run"])
    assert result.exit_code == 0, result.stdout
    assert "best_case" in result.stdout
    assert "06075" in result.stdout
    assert "distance_dominated" in result.stdout
    assert "48105" in result.stdout
    assert "coverage_gap" in result.stdout
    assert "48201" in result.stdout
    assert "wide_prevalence" in result.stdout
    assert "missing_acs" in result.stdout
    assert "Research tool only" in result.stdout
    assert "Dry run only" in result.stdout


def test_demo_plan_no_dry_run() -> None:
    result = runner.invoke(app, ["demo-plan", "--no-dry-run"])
    assert result.exit_code == 0
    assert "Dry run only" not in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "access-gap" in result.stdout


def test_sample_path() -> None:
    result = runner.invoke(app, ["sample-path"])
    assert result.exit_code == 0
    assert "data/sample" in result.stdout.replace("\\", "/")
