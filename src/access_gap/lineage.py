"""Warehouse lineage and dbt-style tests on the committed 3-state slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import duckdb

from access_gap.warehouse import connect_warehouse


@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str


@dataclass
class BuildReport:
    lineage: list[str]
    tests: list[TestResult] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return all(t.passed for t in self.tests)


LINEAGE = [
    "staging.counties ──────────────┐",
    "staging.therapies ─────────────┤",
    "staging.distances ─────────────┤",
    "staging.medicaid_coverage ─────┼── intermediate.county_therapy",
    "staging.acs_insurance ─────────┤         │",
    "staging.prevalence ────────────┘         │",
    "                                         ▼",
    "                                   marts.access_index",
    "staging.* ──────────────────────────► marts.source_row_counts",
    "weights.py (explicit schemes) ──────► score; never a hidden composite",
]


def _count(con: duckdb.DuckDBPyConnection, sql: str) -> int:
    row = con.execute(sql).fetchone()
    assert row is not None
    return int(row[0])


def run_tests(con: duckdb.DuckDBPyConnection) -> list[TestResult]:
    tests: list[TestResult] = []

    n_pairs = _count(con, "SELECT COUNT(*) FROM staging.county_therapy")
    n_unique = _count(
        con, "SELECT COUNT(*) FROM (SELECT DISTINCT fips, therapy_id FROM staging.county_therapy)"
    )
    tests.append(
        TestResult(
            "unique_county_therapy",
            n_pairs == n_unique == 36,
            f"rows={n_pairs} distinct={n_unique}",
        )
    )

    n_null_keys = _count(
        con,
        """
        SELECT COUNT(*) FROM intermediate.county_therapy
        WHERE fips IS NULL OR therapy_id IS NULL
        """,
    )
    tests.append(TestResult("not_null_keys", n_null_keys == 0, f"null keys={n_null_keys}"))

    gilmer = con.execute(
        """
        SELECT insured_pct FROM intermediate.county_therapy
        WHERE fips = '54021' AND therapy_id = 'zolgensma'
        """
    ).fetchone()
    gilmer_null = gilmer is not None and gilmer[0] is None
    tests.append(
        TestResult(
            "acs_never_imputed_to_zero",
            gilmer_null,
            "Gilmer (54021) insured_pct is NULL, not 0",
        )
    )

    n_zero_from_blank = _count(
        con,
        """
        SELECT COUNT(*) FROM staging.acs_insurance
        WHERE (insured_pct IS NULL OR insured_pct = '') AND fips = '54021'
        """,
    )
    tests.append(
        TestResult(
            "gilmer_blank_in_staging",
            n_zero_from_blank == 1,
            f"blank ACS rows for Gilmer={n_zero_from_blank}",
        )
    )

    n_index = _count(con, "SELECT COUNT(*) FROM marts.access_index")
    tests.append(TestResult("index_row_count", n_index == 36, f"index rows={n_index}"))

    n_orphan = _count(
        con,
        """
        SELECT COUNT(*) FROM marts.access_index i
        LEFT JOIN staging.county_therapy ct
          ON ct.fips = i.fips AND ct.therapy_id = i.therapy_id
        WHERE ct.fips IS NULL
        """,
    )
    tests.append(TestResult("index_fk_county_therapy", n_orphan == 0, f"orphans={n_orphan}"))

    n_midpoint = _count(
        con,
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = 'marts' AND column_name ILIKE '%midpoint%'
        """,
    )
    tests.append(
        TestResult(
            "no_silent_prevalence_midpoint",
            n_midpoint == 0,
            "marts has no midpoint column; eligible pop stays an interval",
        )
    )
    return tests


def build(sample_dir: object | None = None) -> tuple[duckdb.DuckDBPyConnection, BuildReport]:
    from pathlib import Path

    path = Path(str(sample_dir)) if sample_dir is not None else None
    con = connect_warehouse(path)
    counts = {
        "staging.counties": _count(con, "SELECT COUNT(*) FROM staging.counties"),
        "staging.therapies": _count(con, "SELECT COUNT(*) FROM staging.therapies"),
        "staging.county_therapy": _count(con, "SELECT COUNT(*) FROM staging.county_therapy"),
        "intermediate.county_therapy": _count(
            con, "SELECT COUNT(*) FROM intermediate.county_therapy"
        ),
        "marts.access_index": _count(con, "SELECT COUNT(*) FROM marts.access_index"),
        "marts.source_row_counts": _count(con, "SELECT COUNT(*) FROM marts.source_row_counts"),
    }
    report = BuildReport(lineage=list(LINEAGE), tests=run_tests(con), row_counts=counts)
    return con, report


def report_as_dict(report: BuildReport) -> dict[str, Any]:
    return {
        "lineage": report.lineage,
        "row_counts": report.row_counts,
        "tests": [{"name": t.name, "passed": t.passed, "detail": t.detail} for t in report.tests],
        "all_passed": report.all_passed,
    }
