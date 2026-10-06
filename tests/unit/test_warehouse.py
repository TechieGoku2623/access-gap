from __future__ import annotations

from access_gap.slice_data import load_slice
from access_gap.warehouse import connect_warehouse


def test_duckdb_staging_row_counts() -> None:
    slice_ = load_slice()
    con = connect_warehouse()
    n_ct = int(con.execute("SELECT COUNT(*) FROM staging.county_therapy").fetchone()[0])
    assert n_ct == len(slice_.pairs) == 36
    n_missing = int(
        con.execute(
            """
            SELECT n_missing FROM marts.source_row_counts
            WHERE source = 'acs_insurance'
            """
        ).fetchone()[0]
    )
    assert n_missing == 1
    n_index = int(con.execute("SELECT COUNT(*) FROM marts.access_index").fetchone()[0])
    assert n_index == 36
    gilmer = con.execute(
        """
        SELECT insured_pct FROM intermediate.county_therapy
        WHERE fips = '54021' AND therapy_id = 'zolgensma'
        """
    ).fetchone()
    assert gilmer[0] is None


def test_slice_lookups() -> None:
    slice_ = load_slice()
    assert slice_.county("06075").name.startswith("San Francisco")
    assert slice_.therapy("casgevy").visit_multiplier == 12
    assert slice_.source("cms_medicaid").retrieved == "2026-01-15"
    assert len(slice_.designed_pairs()) == 5
    try:
        slice_.county("99999")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    try:
        slice_.therapy("nope")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    try:
        slice_.prevalence("06075", "missing")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    try:
        slice_.coverage("99", "zolgensma")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    try:
        slice_.insurance("00000")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    try:
        slice_.distance("00000", "zolgensma")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    try:
        slice_.source("nope")
    except KeyError:
        return
    raise AssertionError("expected KeyError")
