"""Rank correlation of the access index across weight schemes."""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

from access_gap import SPEARMAN_THRESHOLD
from access_gap.index import score_slice, spearman
from access_gap.slice_data import load_slice
from access_gap.weights import SCHEMES

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def main() -> None:
    slice_ = load_slice()
    keyed: dict[str, dict[tuple[str, str], float]] = {}
    incomplete_ids: list[str] = []
    for name, scheme in SCHEMES.items():
        scores = score_slice(slice_, scheme)
        complete: dict[tuple[str, str], float] = {}
        for row in scores:
            key = (row.fips, row.therapy_id)
            if "insurance" in row.missing_components and scheme.insurance > 0:
                incomplete_ids.append(f"{row.fips}×{row.therapy_id}")
                continue
            if row.score is None:
                continue
            complete[key] = row.score
        keyed[name] = complete

    common_keys = set.intersection(*[set(d.keys()) for d in keyed.values()])
    pair_rows: list[dict[str, object]] = []
    table_rows: list[list[str]] = []
    rhos: list[float] = []
    names = list(SCHEMES)
    for left, right in itertools.combinations(names, 2):
        xs = [keyed[left][k] for k in sorted(common_keys)]
        ys = [keyed[right][k] for k in sorted(common_keys)]
        rho = spearman(xs, ys)
        rhos.append(rho)
        pair_rows.append({"left": left, "right": right, "spearman": rho, "n": len(common_keys)})
        table_rows.append([left, right, str(len(common_keys)), pct(rho)])

    min_rho = min(rhos) if rhos else 0.0
    needs_rethink = min_rho < SPEARMAN_THRESHOLD
    decision = (
        "The composite access index needs rethinking; rankings are not "
        f"stable across defensible weight schemes (min Spearman {min_rho:.3f} "
        f"< {SPEARMAN_THRESHOLD:.2f})."
        if needs_rethink
        else (
            f"Rankings are stable enough to keep a composite (min Spearman "
            f"{min_rho:.3f} ≥ {SPEARMAN_THRESHOLD:.2f}). Still publish all schemes."
        )
    )

    geo = score_slice(slice_, SCHEMES["geography_only"])
    cov = score_slice(slice_, SCHEMES["coverage_only"])
    teaching = {}
    for role in ("best_case", "distance_dominated", "coverage_gap"):
        pair = next(p for p in slice_.pairs if p.role == role)
        g = next(s for s in geo if s.fips == pair.fips and s.therapy_id == pair.therapy_id)
        c = next(s for s in cov if s.fips == pair.fips and s.therapy_id == pair.therapy_id)
        teaching[role] = {
            "fips": pair.fips,
            "therapy_id": pair.therapy_id,
            "geography_score": g.score,
            "coverage_score": c.score,
            "effective_miles": g.effective_miles,
        }

    payload = {
        "n_pairs": len(slice_.pairs),
        "n_complete_for_correlation": len(common_keys),
        "spearman_threshold": SPEARMAN_THRESHOLD,
        "min_spearman": min_rho,
        "needs_rethinking": needs_rethink,
        "decision": decision,
        "pairs": pair_rows,
        "teaching_cases": teaching,
        "incomplete_dropped_from_correlation": sorted(set(incomplete_ids)),
        "gold_source": "Committed 3-state slice. National rank correlation is unmeasured.",
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(["scheme A", "scheme B", "n", "Spearman"], table_rows)
    md = (
        "# index_sensitivity results\n\n"
        f"Complete-case n = {len(common_keys)}. Min Spearman = {min_rho:.3f}. "
        f"Needs rethinking: {needs_rethink}.\n\n"
        f"{decision}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
