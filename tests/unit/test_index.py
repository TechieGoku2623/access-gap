from __future__ import annotations

import pytest

from access_gap.index import pearson, ranks, score_row, score_slice, spearman, travel_score
from access_gap.slice_data import load_slice
from access_gap.weights import SCHEMES, get_scheme


def test_multi_visit_not_straight_line() -> None:
    effective, score = travel_score(360.0, 8)
    assert effective == 360.0 * 2 * 8
    assert score < travel_score(14.0, 12)[1]


def test_best_case_beats_distance_on_geography() -> None:
    slice_ = load_slice()
    geo = SCHEMES["geography_only"]
    best = next(p for p in slice_.pairs if p.role == "best_case")
    far = next(p for p in slice_.pairs if p.role == "distance_dominated")
    assert score_row(slice_, best, geo).score > score_row(slice_, far, geo).score  # type: ignore[operator]


def test_coverage_gap_high_geo_low_coverage() -> None:
    slice_ = load_slice()
    pair = next(p for p in slice_.pairs if p.role == "coverage_gap")
    geo = score_row(slice_, pair, SCHEMES["geography_only"])
    cov = score_row(slice_, pair, SCHEMES["coverage_only"])
    assert geo.medicaid_score == 0.0
    assert geo.score is not None and geo.score > 0.25
    assert cov.score is not None and cov.score < 0.3


def test_missing_acs_not_imputed_to_zero() -> None:
    slice_ = load_slice()
    pair = next(p for p in slice_.pairs if p.role == "missing_acs")
    scored = score_row(slice_, pair, SCHEMES["default"])
    assert scored.insurance_score is None
    assert "insurance" in scored.missing_components
    assert scored.incomplete is True
    zeroed = 0.0
    assert scored.score != zeroed


def test_get_scheme_unknown() -> None:
    with pytest.raises(KeyError):
        get_scheme("not-a-scheme")


def test_spearman_and_empty_pearson() -> None:
    assert abs(spearman([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-9
    assert pearson([], []) == 0.0
    assert pearson([1.0, 1.0], [2.0, 3.0]) == 0.0
    with pytest.raises(ValueError):
        spearman([1.0], [1.0, 2.0])
    assert ranks([3.0, 1.0, 1.0])[1] == ranks([3.0, 1.0, 1.0])[2]


def test_score_slice_length() -> None:
    slice_ = load_slice()
    rows = score_slice(slice_, SCHEMES["default"])
    assert len(rows) == 36


def test_normalized_empty_scheme() -> None:
    scheme = SCHEMES["geography_only"]
    assert scheme.normalized(set()) == {}
    empty_available = scheme.normalized({"medicaid"})
    assert empty_available == {}


def test_capacity_only_scheme_on_center_without_slots() -> None:
    from access_gap.schemas import WeightScheme

    slice_ = load_slice()
    pair = next(p for p in slice_.pairs if p.role == "missing_acs")
    scheme = WeightScheme(name="cap_only", travel=0.0, medicaid=0.0, insurance=0.0, capacity=1.0)
    scored = score_row(slice_, pair, scheme)
    assert scored.score is None
    assert scored.incomplete is True
    assert slice_.capacity_for("cchmc") is None
