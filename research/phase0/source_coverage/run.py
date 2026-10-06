"""Per-source freshness, completeness, and missingness on the 3-state slice."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from access_gap import COMPLETENESS_THRESHOLD, EVAL_DATE
from access_gap.slice_data import load_slice
from access_gap.warehouse import connect_warehouse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _freshness_days(retrieved: str) -> int:
    got = date.fromisoformat(retrieved)
    ev = date.fromisoformat(EVAL_DATE)
    return (ev - got).days


def main() -> None:
    slice_ = load_slice()
    con = connect_warehouse()
    counts = {
        str(row[0]): (int(row[1]), int(row[2]))
        for row in con.execute(
            "SELECT source, n, n_missing FROM marts.source_row_counts"
        ).fetchall()
    }
    n_counties = len(slice_.counties)
    n_pairs = len(slice_.pairs)

    reports: list[dict[str, object]] = []
    table_rows: list[list[str]] = []
    usable: list[str] = []
    unusable: list[str] = []

    specs = [
        (
            "cms_medicaid",
            "medicaid_coverage",
            3 * len(slice_.therapies),
            counts["medicaid_coverage"][1],
        ),
        ("acs_s2701", "acs_insurance", n_counties, counts["acs_insurance"][1]),
        ("travel_standin", "distances", n_pairs, counts["distances"][1]),
        ("orphanet_cdc", "prevalence", counts["prevalence"][0], 0),
        (
            "capacity_sparse",
            "capacity",
            len(slice_.centers),
            len(slice_.centers) - len(slice_.capacities),
        ),
        ("gazetteer", "counties", n_counties, 0),
        ("center_list", "centers", len(slice_.centers), 0),
    ]
    for source_id, table, expected, n_missing in specs:
        src = slice_.source(source_id)
        n = counts.get(table, (expected, n_missing))[0]
        completeness = (n - n_missing) / n if n else 0.0
        fresh = _freshness_days(src.retrieved)
        is_usable = completeness >= COMPLETENESS_THRESHOLD and fresh <= 365
        decision = "usable" if is_usable else "not usable as a primary index input"
        if source_id == "acs_s2701" and n_missing > 0 and is_usable:
            decision = "usable with explicit missing handling (never impute zero)"
        if is_usable:
            usable.append(source_id)
        else:
            unusable.append(source_id)
        reports.append(
            {
                "source_id": source_id,
                "table": table,
                "retrieved": src.retrieved,
                "freshness_days": fresh,
                "n": n,
                "n_missing": n_missing,
                "completeness": completeness,
                "usable": is_usable,
                "decision": decision,
            }
        )
        table_rows.append(
            [
                source_id,
                src.retrieved,
                str(fresh),
                str(n),
                str(n_missing),
                pct(completeness),
                decision,
            ]
        )

    gilmer = slice_.insurance("54021")
    payload = {
        "evaluation_date": EVAL_DATE,
        "n_counties": n_counties,
        "n_pairs": n_pairs,
        "completeness_threshold": COMPLETENESS_THRESHOLD,
        "usable_sources": usable,
        "unusable_sources": unusable,
        "sources": reports,
        "gilmer_insured_pct_is_null": gilmer.insured_pct is None,
        "decision": (
            "Usable: "
            + ", ".join(usable)
            + ". Not usable as a primary index input: "
            + (", ".join(unusable) or "(none)")
            + ". ACS missingness on Gilmer is kept as missing."
        ),
        "gold_source": (
            "Committed 3-state slice. Not a live CMS or Census pull. "
            "Replacing the slice with a dated national extract is the "
            "measurement that would retire that limitation."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        ["source", "retrieved", "freshness days", "n", "n missing", "completeness", "decision"],
        table_rows,
    )
    md = (
        "# source_coverage results\n\n"
        f"Evaluation date {EVAL_DATE}. Counties = {n_counties}. "
        f"County × therapy rows = {n_pairs}.\n\n"
        f"{payload['decision']}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
