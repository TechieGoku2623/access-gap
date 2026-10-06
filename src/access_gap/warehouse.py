"""dbt-style DuckDB warehouse: staging → intermediate → marts."""

from __future__ import annotations

from pathlib import Path

import duckdb

from access_gap.config import get_settings
from access_gap.index import score_slice
from access_gap.slice_data import load_slice
from access_gap.weights import SCHEMES


def connect_warehouse(sample_dir: Path | None = None) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with staged sample tables and completeness marts."""

    root = sample_dir or get_settings().sample_dir
    con = duckdb.connect(":memory:")
    con.execute("CREATE SCHEMA staging")
    con.execute("CREATE SCHEMA intermediate")
    con.execute("CREATE SCHEMA marts")
    _stage_csv(con, "staging.counties", root / "counties.csv")
    _stage_csv(con, "staging.therapies", root / "therapies.csv")
    _stage_csv(con, "staging.centers", root / "centers.csv")
    _stage_csv(con, "staging.medicaid_coverage", root / "medicaid_coverage.csv")
    _stage_csv(con, "staging.acs_insurance", root / "acs_insurance.csv")
    _stage_csv(con, "staging.prevalence", root / "prevalence.csv")
    _stage_csv(con, "staging.distances", root / "distances.csv")
    _stage_csv(con, "staging.capacity", root / "capacity.csv")
    _stage_csv(con, "staging.county_therapy", root / "county_therapy.csv")
    con.execute(
        """
        CREATE VIEW intermediate.county_therapy AS
        SELECT
          ct.fips,
          ct.therapy_id,
          ct.role,
          c.name AS county_name,
          c.state,
          c.population,
          t.visit_multiplier,
              TRY_CAST(d.one_way_miles AS DOUBLE) AS one_way_miles,
              TRY_CAST(d.one_way_miles AS DOUBLE) * 2
                * TRY_CAST(t.visit_multiplier AS INTEGER) AS effective_miles,
          m.covered AS medicaid_covered,
          TRY_CAST(a.insured_pct AS DOUBLE) AS insured_pct
        FROM staging.county_therapy ct
        JOIN staging.counties c ON c.fips = ct.fips
        JOIN staging.therapies t ON t.therapy_id = ct.therapy_id
        JOIN staging.distances d
          ON d.fips = ct.fips AND d.therapy_id = ct.therapy_id
        JOIN staging.medicaid_coverage m
          ON m.state_fips = c.state_fips AND m.therapy_id = ct.therapy_id
        LEFT JOIN staging.acs_insurance a ON a.fips = ct.fips
        """
    )
    _load_index_mart(con, root)
    con.execute(
        """
        CREATE VIEW marts.source_row_counts AS
        SELECT 'counties' AS source, COUNT(*) AS n, 0 AS n_missing FROM staging.counties
        UNION ALL
        SELECT 'therapies', COUNT(*), 0 FROM staging.therapies
        UNION ALL
        SELECT 'medicaid_coverage', COUNT(*), 0 FROM staging.medicaid_coverage
        UNION ALL
        SELECT
          'acs_insurance',
          COUNT(*),
          SUM(CASE WHEN insured_pct IS NULL OR insured_pct = '' THEN 1 ELSE 0 END)
        FROM staging.acs_insurance
        UNION ALL
        SELECT 'distances', COUNT(*), 0 FROM staging.distances
        UNION ALL
        SELECT 'prevalence', COUNT(*), 0 FROM staging.prevalence
        UNION ALL
        SELECT 'capacity', COUNT(*), 0 FROM staging.capacity
        UNION ALL
        SELECT 'county_therapy', COUNT(*), 0 FROM staging.county_therapy
        """
    )
    return con


def _stage_csv(con: duckdb.DuckDBPyConnection, table: str, path: Path) -> None:
    con.execute(
        f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto(?, HEADER=TRUE, ALL_VARCHAR=TRUE)",
        [path.as_posix()],
    )


def _load_index_mart(con: duckdb.DuckDBPyConnection, sample_dir: Path) -> None:
    slice_ = load_slice(sample_dir)
    default = SCHEMES["default"]
    rows = score_slice(slice_, default)
    con.execute(
        """
        CREATE TABLE marts.access_index (
          fips VARCHAR,
          therapy_id VARCHAR,
          scheme VARCHAR,
          score DOUBLE,
          incomplete BOOLEAN,
          effective_miles DOUBLE,
          travel_score DOUBLE,
          medicaid_score DOUBLE,
          insurance_score DOUBLE
        )
        """
    )
    for row in rows:
        con.execute(
            """
            INSERT INTO marts.access_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row.fips,
                row.therapy_id,
                row.scheme,
                row.score,
                row.incomplete,
                row.effective_miles,
                row.travel_score,
                row.medicaid_score,
                row.insurance_score,
            ],
        )
