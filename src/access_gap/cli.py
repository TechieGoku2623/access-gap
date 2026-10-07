"""Phase 0–3 CLI. Committed 3-state slice. Access index is fully transparent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from access_gap import SAFETY_DISCLAIMER, __version__
from access_gap.config import get_settings
from access_gap.county_view import county_payload, designed_side_by_side, movers_for_therapy
from access_gap.lineage import build
from access_gap.logging import configure_logging
from access_gap.report import write_report
from access_gap.slice_data import load_slice

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=100)


@app.callback()
def _main() -> None:
    configure_logging()


def _print_disclaimer() -> None:
    console.print(SAFETY_DISCLAIMER)


@app.command("version")
def version() -> None:
    """Print the package version."""

    console.print(f"access-gap {__version__}")


@app.command("demo-plan")
def demo_plan(
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Print the five designed county × therapy cases and the path each exercises."""

    slice_ = load_slice()
    console.print("[bold]access-gap designed county × therapy cases[/bold]\n")
    for pair in slice_.designed_pairs():
        county = slice_.county(pair.fips)
        therapy = slice_.therapy(pair.therapy_id)
        console.print(
            f"[bold]{pair.role}[/bold]  {county.fips} {county.name}, {county.state}  "
            f"× {therapy.therapy_id}"
        )
        console.print(f"  path:     {pair.path_exercised}")
        console.print(f"  expected: {pair.expected_behavior}\n")
    console.print()
    _print_disclaimer()
    if dry_run:
        console.print(
            "\nDry run only. `make demo` runs demo-build, county decomposition, "
            "sensitivity, and the choropleth report."
        )
    console.print(f"Sample directory: {get_settings().sample_dir}")


@app.command("demo-build")
def demo_build(
    sample_dir: Path | None = typer.Option(None, "--sample-dir"),
    summary: bool = typer.Option(False, "--summary", help="Lineage + test verdict only"),
) -> None:
    """Build staging → intermediate → marts and print lineage plus tests."""

    _con, report = build(sample_dir)
    console.print("[bold]access-gap demo-build[/bold]")
    console.print("DuckDB dbt-style: staging → intermediate → marts\n")
    console.print("[bold]Lineage[/bold]")
    for line in report.lineage:
        console.print(line)
    if not summary:
        console.print()
        counts = Table(title="Row counts")
        counts.add_column("relation")
        counts.add_column("n", justify="right")
        for name, n in report.row_counts.items():
            counts.add_row(name, str(n))
        console.print(counts)
        tests = Table(title="Warehouse tests")
        tests.add_column("test")
        tests.add_column("result")
        tests.add_column("detail")
        for row in report.tests:
            tests.add_row(row.name, "PASS" if row.passed else "FAIL", row.detail)
        console.print(tests)
    else:
        failed = [row.name for row in report.tests if not row.passed]
        console.print(f"warehouse tests: {len(report.tests)}  failed: {failed or '(none)'}")
    if not report.all_passed:
        console.print("One or more warehouse tests failed.")
        _print_disclaimer()
        raise typer.Exit(code=1)
    console.print("All warehouse tests passed. ACS blanks stay blank; never imputed to zero.")
    _print_disclaimer()


def _print_county(payload: dict[str, Any]) -> None:
    elig = payload["eligible_pop"]
    prev = payload["prevalence_per_100k"]
    assert isinstance(elig, dict)
    assert isinstance(prev, dict)
    console.print(
        f"[bold]{payload['fips']}[/bold]  {payload['county']}, {payload['state']}  "
        f"× {payload['therapy_id']}  ({payload['role']})"
    )
    console.print(f"  rural:            {payload['rural']}")
    console.print(
        f"  distance:         {payload['one_way_miles']} mi one-way → "
        f"{payload['effective_miles']} effective mi "
        f"(×2 × {payload['visit_multiplier']} visits)  "
        f"nearest={payload['nearest_center_id']}"
    )
    covered = "covered" if payload["medicaid_covered"] else "NOT covered"
    console.print(f"  medicaid:         {covered}")
    if payload["insured_missing"]:
        console.print("  ACS insured_pct:  MISSING (not imputed to 0)")
    else:
        console.print(f"  ACS insured_pct:  {payload['insured_pct']}")
    console.print(
        f"  prevalence/100k:  [{prev['low']}, {prev['high']}]  ratio={float(prev['ratio']):.3f}"
    )
    console.print(
        f"  eligible pop:     [{float(elig['low']):.2f}, {float(elig['high']):.2f}]  "
        f"INTERVAL  ratio={float(elig['ratio']):.3f}  (no midpoint stored)"
    )
    score = payload["index"]
    score_txt = "—" if score is None else f"{float(score):.3f}"
    console.print(
        f"  index ({payload['scheme']}): {score_txt}  "
        f"incomplete={payload['incomplete']}  "
        f"missing={payload['missing_components']}"
    )
    contribs = payload["contributions"]
    assert isinstance(contribs, dict)
    table = Table(title="Component contributions (transparent weights)")
    table.add_column("component")
    table.add_column("weight", justify="right")
    table.add_column("score", justify="right")
    table.add_column("contribution", justify="right")
    for name, cell in contribs.items():
        assert isinstance(cell, dict)
        w = "—" if cell["weight"] is None else f"{float(cell['weight']):.3f}"
        s = "—" if cell["score"] is None else f"{float(cell['score']):.3f}"
        c = "—" if cell["contribution"] is None else f"{float(cell['contribution']):.3f}"
        table.add_row(name, w, s, c)
    console.print(table)
    console.print("  imputed_acs_to_zero: false   silent_point_estimate: false")


def _print_county_summary(payload: dict[str, Any]) -> None:
    covered = "covered" if payload["medicaid_covered"] else "NOT covered"
    score = payload["index"]
    score_txt = "—" if score is None else f"{float(score):.3f}"
    console.print(
        f"[bold]{payload['fips']}[/bold]  {payload['county']}, {payload['state']}  "
        f"× {payload['therapy_id']}  ({payload['role']})  index={score_txt}"
    )
    insured = "MISSING" if payload["insured_missing"] else str(payload["insured_pct"])
    console.print(
        f"  medicaid: {covered}   distance: {payload['one_way_miles']} mi   insured={insured}"
    )
    contribs = payload["contributions"]
    assert isinstance(contribs, dict)
    parts: list[str] = []
    for name, cell in contribs.items():
        assert isinstance(cell, dict)
        if cell["contribution"] is None:
            continue
        parts.append(f"{name} {float(cell['contribution']):.3f}")
    console.print(f"  components: {', '.join(parts)}")


@app.command("county")
def county(
    fips: list[str] | None = typer.Option(
        None,
        "--fips",
        help="County FIPS. Repeat for side-by-side. Default: designed triple.",
    ),
    therapy: str | None = typer.Option(
        None,
        "--therapy",
        help="Therapy id (zolgensma, casgevy, luxturna). Required with --fips.",
    ),
    scheme: str = typer.Option("default", "--scheme"),
    compare: bool = typer.Option(
        False,
        "--compare/--no-compare",
        help="Print the designed best-case / rural / no-coverage triple.",
    ),
    summary: bool = typer.Option(False, "--summary", help="Index, barrier, and component totals"),
) -> None:
    """Distance, coverage, eligible-pop interval, and index contributions."""

    slice_ = load_slice()
    console.print("[bold]access-gap county[/bold]")
    if compare or not fips:
        if fips and therapy:
            rows = [county_payload(slice_, code, therapy, scheme) for code in fips]
        else:
            rows = designed_side_by_side(slice_)
            if not summary:
                console.print(
                    "Designed side-by-side: 06075×zolgensma (best-case), "
                    "48105×zolgensma (rural / distance), "
                    "48201×casgevy (no Medicaid coverage).\n"
                )
    else:
        if therapy is None:
            raise typer.BadParameter("--therapy is required when --fips is set")
        rows = [county_payload(slice_, code, therapy, scheme) for code in fips]
    printer = _print_county_summary if summary else _print_county
    for i, row in enumerate(rows):
        if i:
            console.print()
        printer(row)
    _print_disclaimer()


@app.command("sensitivity")
def sensitivity(
    therapy: str = typer.Option(..., "--therapy", help="Therapy id to rank."),
    summary: bool = typer.Option(False, "--summary", help="Min Spearman + top movers"),
) -> None:
    """Rank correlation across weight schemes and counties that move most."""

    slice_ = load_slice()
    payload = movers_for_therapy(slice_, therapy)
    console.print(f"[bold]access-gap sensitivity[/bold]  therapy={therapy}")
    console.print(
        f"counties={payload['n_counties']}  complete-case n={payload['n_complete']}  "
        f"min Spearman={float(payload['min_spearman']):.3f}"
    )
    if not summary:
        table = Table(title="Pairwise Spearman (complete cases)")
        table.add_column("scheme A")
        table.add_column("scheme B")
        table.add_column("n", justify="right")
        table.add_column("ρ", justify="right")
        for row in payload["correlations"]:
            assert isinstance(row, dict)
            table.add_row(
                str(row["scheme_a"]),
                str(row["scheme_b"]),
                str(row["n"]),
                f"{float(row['spearman']):.3f}",
            )
        console.print(table)
        movers = Table(title="Counties that move most (max rank shift vs default)")
        movers.add_column("fips")
        movers.add_column("name")
        movers.add_column("rural")
        movers.add_column("rank default", justify="right")
        movers.add_column("rank geo", justify="right")
        movers.add_column("rank coverage", justify="right")
        movers.add_column("max shift", justify="right")
        for row in payload["movers"][:8]:
            assert isinstance(row, dict)
            movers.add_row(
                str(row["fips"]),
                str(row["name"]),
                "yes" if row["rural"] else "no",
                str(int(row["rank_default"])) if row["rank_default"] is not None else "—",
                str(int(row["rank_geography"])) if row["rank_geography"] is not None else "—",
                str(int(row["rank_coverage"])) if row["rank_coverage"] is not None else "—",
                f"{float(row['max_rank_shift']):.0f}",
            )
        console.print(movers)
    else:
        console.print("Counties that move most (max rank shift vs default):")
        for row in payload["movers"][:4]:
            assert isinstance(row, dict)
            console.print(
                f"  {row['fips']}  {row['name']}  shift={float(row['max_rank_shift']):.0f}"
            )
    if float(payload["min_spearman"]) < 0.70:
        console.print(
            "Index needs rethinking: min Spearman < 0.70. "
            "Weights stay explicit; no unpublished composite."
        )
    _print_disclaimer()


@app.command("report")
def report_cmd(
    dest: Path | None = typer.Option(None, "--dest"),
    therapy: str = typer.Option("zolgensma", "--therapy"),
    summary: bool = typer.Option(False, "--summary"),
) -> None:
    """Write a county choropleth HTML file from the sample slice."""

    out = dest or (get_settings().repo_root / "docs" / "report.html")
    path = write_report(out, therapy_id=therapy)
    console.print(f"Wrote choropleth to {path}")
    console.print("Schematic CA / TX / WV panels. Hatched = missing ACS (not zero).")
    if summary:
        ev = get_settings().repo_root / "docs" / "EVALUATION.md"
        n = 0
        for line in ev.read_text(encoding="utf-8").splitlines():
            if line.startswith("# Evaluation"):
                continue
            console.print(line[:100])
            if line.strip():
                n += 1
            if n >= 10:
                break
    _print_disclaimer()


@app.command("demo")
def demo() -> None:
    """Full walkthrough: build, three counties, sensitivity, map. No credentials."""

    console.print("[bold]access-gap demo[/bold]  (committed slice; no credentials)\n")
    demo_build(sample_dir=None)
    console.print()
    county(fips=None, therapy=None, scheme="default", compare=True)
    console.print()
    sensitivity(therapy="zolgensma")
    console.print()
    report_cmd(dest=None, therapy="zolgensma")
    console.print()
    _print_disclaimer()


@app.command("sample-path")
def sample_path() -> None:
    """Print the committed sample directory path."""

    console.print(str(get_settings().sample_dir.resolve()))


if __name__ == "__main__":
    app()
