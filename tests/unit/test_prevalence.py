from __future__ import annotations

from access_gap.prevalence import eligible_population, prevalence_interval
from access_gap.schemas import Interval
from access_gap.slice_data import load_slice


def test_mcdowell_luxturna_is_ten_x() -> None:
    slice_ = load_slice()
    interval = prevalence_interval(slice_, "54047", "luxturna")
    assert interval.ratio == 10.0
    elig = eligible_population(slice_, "54047", "luxturna")
    assert abs(elig.high / elig.low - 10.0) < 1e-9
    assert elig.low != elig.midpoint_explicit()


def test_interval_infinite_ratio() -> None:
    assert Interval(low=0.0, high=1.0).ratio == float("inf")


def test_general_prevalence_used_when_no_override() -> None:
    slice_ = load_slice()
    interval = prevalence_interval(slice_, "06075", "zolgensma")
    assert interval.low == 8.0
    assert interval.high == 10.0
