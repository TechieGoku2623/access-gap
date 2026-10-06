"""Explicit, configurable access-index weights.

Capacity is in the schema so a later extract can use it. Default weight
is 0 because source_coverage marks that table unusable on this slice.
"""

from __future__ import annotations

from access_gap.schemas import WeightScheme

SCHEMES: dict[str, WeightScheme] = {
    "default": WeightScheme(
        name="default", travel=0.40, medicaid=0.35, insurance=0.25, capacity=0.0
    ),
    "equal": WeightScheme(
        name="equal", travel=1.0 / 3.0, medicaid=1.0 / 3.0, insurance=1.0 / 3.0, capacity=0.0
    ),
    "geography_only": WeightScheme(
        name="geography_only", travel=1.0, medicaid=0.0, insurance=0.0, capacity=0.0
    ),
    "coverage_only": WeightScheme(
        name="coverage_only", travel=0.0, medicaid=0.70, insurance=0.30, capacity=0.0
    ),
    "travel_heavy": WeightScheme(
        name="travel_heavy", travel=0.70, medicaid=0.15, insurance=0.15, capacity=0.0
    ),
}


def get_scheme(name: str) -> WeightScheme:
    try:
        return SCHEMES[name]
    except KeyError as exc:
        raise KeyError(f"unknown weight scheme {name!r}") from exc
