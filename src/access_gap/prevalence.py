"""Prevalence as an interval. Never a silent point estimate."""

from __future__ import annotations

from access_gap.schemas import Interval
from access_gap.slice_data import Slice


def prevalence_interval(slice_: Slice, fips: str, therapy_id: str) -> Interval:
    bound = slice_.prevalence(fips, therapy_id)
    return Interval(low=bound.prev_low_per_100k, high=bound.prev_high_per_100k)


def eligible_population(slice_: Slice, fips: str, therapy_id: str) -> Interval:
    """County population × published prevalence range, per 100k.

    Returns an interval. There is no default midpoint.
    """

    county = slice_.county(fips)
    prev = prevalence_interval(slice_, fips, therapy_id)
    scale = county.population / 100_000.0
    return Interval(low=prev.low * scale, high=prev.high * scale)
