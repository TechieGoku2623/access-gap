"""County × therapy access index. Travel burden is multi-visit."""

from __future__ import annotations

from collections.abc import Sequence

from access_gap.schemas import AccessScore, CountyTherapy, WeightScheme
from access_gap.slice_data import Slice


def travel_score(one_way_miles: float, visit_multiplier: int) -> tuple[float, float]:
    """Return (effective_miles, score in (0, 1]).

    Effective miles = one_way * 2 * visit_multiplier. A one-shot
    straight-line mile is the wrong unit for gene-therapy follow-up.
    """

    effective = one_way_miles * 2.0 * float(visit_multiplier)
    return effective, 1.0 / (1.0 + effective / 150.0)


def score_row(
    slice_: Slice,
    pair: CountyTherapy,
    scheme: WeightScheme,
) -> AccessScore:
    therapy = slice_.therapy(pair.therapy_id)
    distance = slice_.distance(pair.fips, pair.therapy_id)
    coverage = slice_.coverage(slice_.county(pair.fips).state_fips, pair.therapy_id)
    insurance = slice_.insurance(pair.fips)
    effective, t_score = travel_score(distance.one_way_miles, therapy.visit_multiplier)
    m_score = 1.0 if coverage.covered else 0.0
    i_score = insurance.insured_pct
    cap_score: float | None = None
    missing: list[str] = []
    available = {"travel", "medicaid"}
    if i_score is None:
        missing.append("insurance")
    else:
        available.add("insurance")
    center_cap = slice_.capacity_for(distance.nearest_center_id)
    if center_cap is None:
        missing.append("capacity")
    else:
        cap_score = min(1.0, center_cap.slots_per_month / 20.0)
        available.add("capacity")

    weights = scheme.normalized(available)
    if not weights:
        return AccessScore(
            fips=pair.fips,
            therapy_id=pair.therapy_id,
            scheme=scheme.name,
            score=None,
            incomplete=True,
            missing_components=missing,
            effective_miles=effective,
            travel_score=t_score,
            medicaid_score=m_score,
            insurance_score=i_score,
            capacity_score=cap_score,
        )
    total = 0.0
    total += weights.get("travel", 0.0) * t_score
    total += weights.get("medicaid", 0.0) * m_score
    if i_score is not None:
        total += weights.get("insurance", 0.0) * i_score
    if cap_score is not None:
        total += weights.get("capacity", 0.0) * cap_score
    return AccessScore(
        fips=pair.fips,
        therapy_id=pair.therapy_id,
        scheme=scheme.name,
        score=total,
        incomplete=bool(missing),
        missing_components=missing,
        effective_miles=effective,
        travel_score=t_score,
        medicaid_score=m_score,
        insurance_score=i_score,
        capacity_score=cap_score,
    )


def score_slice(slice_: Slice, scheme: WeightScheme) -> list[AccessScore]:
    return [score_row(slice_, pair, scheme) for pair in slice_.pairs]


def ranks(values: Sequence[float]) -> list[float]:
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    out = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n == 0:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0.0 or den_y == 0.0:
        return 0.0
    return float(num / (den_x * den_y))


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys):
        raise ValueError("spearman requires equal-length vectors")
    return pearson(ranks(xs), ranks(ys))
