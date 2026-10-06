"""Propagate published prevalence intervals. Never a silent point estimate."""

from __future__ import annotations

import sys
from pathlib import Path

from access_gap import WIDE_PREVALENCE_RATIO
from access_gap.prevalence import eligible_population, prevalence_interval
from access_gap.slice_data import load_slice

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def main() -> None:
    slice_ = load_slice()
    rows: list[dict[str, object]] = []
    table_rows: list[list[str]] = []
    wide: list[str] = []
    for pair in slice_.pairs:
        prev = prevalence_interval(slice_, pair.fips, pair.therapy_id)
        elig = eligible_population(slice_, pair.fips, pair.therapy_id)
        is_wide = prev.ratio >= WIDE_PREVALENCE_RATIO
        if is_wide:
            wide.append(f"{pair.fips}×{pair.therapy_id}")
        rec = {
            "fips": pair.fips,
            "therapy_id": pair.therapy_id,
            "role": pair.role,
            "prev_low_per_100k": prev.low,
            "prev_high_per_100k": prev.high,
            "ratio": prev.ratio,
            "eligible_low": elig.low,
            "eligible_high": elig.high,
            "wide": is_wide,
            "used_midpoint": False,
        }
        rows.append(rec)
        if pair.role != "filler":
            table_rows.append(
                [
                    pair.role,
                    pair.fips,
                    pair.therapy_id,
                    f"{prev.low:g}",
                    f"{prev.high:g}",
                    pct(prev.ratio),
                    f"{elig.low:.2f}",
                    f"{elig.high:.2f}",
                    "interval" if is_wide else "narrower interval",
                ]
            )

    mcdowell = next(r for r in rows if r["role"] == "wide_prevalence")
    decision = (
        f"{len(set(wide))} county×therapy pair(s) have a published prevalence "
        f"range ≥ {WIDE_PREVALENCE_RATIO:.0f}× "
        f"({', '.join(sorted(set(wide)))}). Eligible population is an "
        "interval. Phase 2 must not pick a silent point estimate."
    )
    payload = {
        "n_pairs": len(rows),
        "wide_ratio_threshold": WIDE_PREVALENCE_RATIO,
        "n_wide": len(set(wide)),
        "wide_ids": sorted(set(wide)),
        "used_silent_point_estimate": False,
        "mcdowell_luxturna_ratio": mcdowell["ratio"],
        "decision": decision,
        "rows": rows,
        "gold_source": (
            "Committed published-range stand-ins (retrieved 2026-01-15). "
            "Live Orphanet/CDC refresh is unmeasured."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        [
            "role",
            "fips",
            "therapy",
            "prev low /100k",
            "prev high /100k",
            "ratio",
            "eligible low",
            "eligible high",
            "form",
        ],
        table_rows,
    )
    md = (
        "# prevalence_bounds results\n\n"
        f"Silent point estimate used: false. Wide pairs: {len(set(wide))}.\n\n"
        f"{decision}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
