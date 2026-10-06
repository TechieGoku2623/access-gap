"""Transparent county × therapy decomposition. Eligible pop is an interval."""

from __future__ import annotations

from typing import Any

from access_gap.index import score_row
from access_gap.prevalence import eligible_population, prevalence_interval
from access_gap.schemas import AccessScore, WeightScheme
from access_gap.slice_data import Slice
from access_gap.weights import SCHEMES, get_scheme


def contributions(score: AccessScore, scheme: WeightScheme) -> dict[str, dict[str, float | None]]:
    """Weight × component score after dropping missing inputs (never zero-filled)."""

    available = {"travel", "medicaid"}
    if score.insurance_score is not None:
        available.add("insurance")
    if score.capacity_score is not None:
        available.add("capacity")
    weights = scheme.normalized(available)
    out: dict[str, dict[str, float | None]] = {}
    raw = {
        "travel": score.travel_score,
        "medicaid": score.medicaid_score,
        "insurance": score.insurance_score,
        "capacity": score.capacity_score,
    }
    for name, value in raw.items():
        weight = weights.get(name)
        contrib = None if weight is None or value is None else weight * value
        out[name] = {"weight": weight, "score": value, "contribution": contrib}
    return out


def county_payload(
    slice_: Slice,
    fips: str,
    therapy_id: str,
    scheme_name: str = "default",
) -> dict[str, Any]:
    county = slice_.county(fips)
    therapy = slice_.therapy(therapy_id)
    pair = next(
        (p for p in slice_.pairs if p.fips == fips and p.therapy_id == therapy_id),
        None,
    )
    if pair is None:
        raise KeyError((fips, therapy_id))
    scheme = get_scheme(scheme_name)
    scored = score_row(slice_, pair, scheme)
    distance = slice_.distance(fips, therapy_id)
    coverage = slice_.coverage(county.state_fips, therapy_id)
    insurance = slice_.insurance(fips)
    prev = prevalence_interval(slice_, fips, therapy_id)
    elig = eligible_population(slice_, fips, therapy_id)
    return {
        "fips": fips,
        "county": county.name,
        "state": county.state,
        "rural": county.rural,
        "population": county.population,
        "therapy_id": therapy_id,
        "therapy_name": therapy.name,
        "role": pair.role,
        "path": pair.path_exercised,
        "one_way_miles": distance.one_way_miles,
        "visit_multiplier": therapy.visit_multiplier,
        "effective_miles": scored.effective_miles,
        "nearest_center_id": distance.nearest_center_id,
        "medicaid_covered": coverage.covered,
        "insured_pct": insurance.insured_pct,
        "insured_missing": insurance.insured_pct is None,
        "prevalence_per_100k": {"low": prev.low, "high": prev.high, "ratio": prev.ratio},
        "eligible_pop": {"low": elig.low, "high": elig.high, "ratio": elig.ratio},
        "scheme": scheme.name,
        "index": scored.score,
        "incomplete": scored.incomplete,
        "missing_components": scored.missing_components,
        "contributions": contributions(scored, scheme),
        "imputed_acs_to_zero": False,
        "silent_point_estimate": False,
    }


def designed_side_by_side(slice_: Slice) -> list[dict[str, Any]]:
    """Best-case, rural/distance, and no-coverage rows next to each other."""

    triples = (
        ("06075", "zolgensma"),
        ("48105", "zolgensma"),
        ("48201", "casgevy"),
    )
    return [county_payload(slice_, fips, therapy) for fips, therapy in triples]


def movers_for_therapy(slice_: Slice, therapy_id: str) -> dict[str, Any]:
    """Spearman across schemes plus counties whose rank moves the most."""

    from access_gap.index import spearman

    pairs = [p for p in slice_.pairs if p.therapy_id == therapy_id]
    if not pairs:
        raise KeyError(therapy_id)
    scheme_scores: dict[str, list[float | None]] = {}
    fips_order = [p.fips for p in pairs]
    for name, scheme in SCHEMES.items():
        rows = [score_row(slice_, p, scheme) for p in pairs]
        scheme_scores[name] = [r.score for r in rows]

    complete_idx = [
        i for i in range(len(pairs)) if all(scheme_scores[name][i] is not None for name in SCHEMES)
    ]
    correlations: list[dict[str, Any]] = []
    names = list(SCHEMES)
    min_rho = 1.0
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            xs = [float(scheme_scores[a][k]) for k in complete_idx]  # type: ignore[arg-type]
            ys = [float(scheme_scores[b][k]) for k in complete_idx]  # type: ignore[arg-type]
            rho = spearman(xs, ys) if xs else 0.0
            min_rho = min(min_rho, rho)
            correlations.append({"scheme_a": a, "scheme_b": b, "n": len(xs), "spearman": rho})

    # Rank within therapy under default vs geography_only vs coverage_only.
    def _ranks(values: list[float | None]) -> list[float | None]:
        present = [(i, v) for i, v in enumerate(values) if v is not None]
        order = sorted(present, key=lambda item: item[1], reverse=True)
        ranks: list[float | None] = [None] * len(values)
        for rank, (idx, _) in enumerate(order, start=1):
            ranks[idx] = float(rank)
        return ranks

    default_r = _ranks(scheme_scores["default"])
    geo_r = _ranks(scheme_scores["geography_only"])
    cov_r = _ranks(scheme_scores["coverage_only"])
    moves: list[dict[str, Any]] = []
    for i, fips in enumerate(fips_order):
        if default_r[i] is None:
            continue
        span = 0.0
        if geo_r[i] is not None:
            span = max(span, abs(default_r[i] - geo_r[i]))  # type: ignore[operator]
        if cov_r[i] is not None:
            span = max(span, abs(default_r[i] - cov_r[i]))  # type: ignore[operator]
        county = slice_.county(fips)
        moves.append(
            {
                "fips": fips,
                "name": county.name,
                "rural": county.rural,
                "rank_default": default_r[i],
                "rank_geography": geo_r[i],
                "rank_coverage": cov_r[i],
                "max_rank_shift": span,
            }
        )
    moves.sort(key=lambda row: float(row["max_rank_shift"]), reverse=True)
    return {
        "therapy_id": therapy_id,
        "n_counties": len(pairs),
        "n_complete": len(complete_idx),
        "min_spearman": min_rho,
        "correlations": correlations,
        "movers": moves,
    }
