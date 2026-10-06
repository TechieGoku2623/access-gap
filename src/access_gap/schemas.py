"""Data contracts for the committed 3-state county × therapy slice."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceManifest(BaseModel):
    id: str
    name: str
    url: str
    retrieved: str
    license: str
    notes: str


class County(BaseModel):
    fips: str
    name: str
    state: str
    state_fips: str
    population: int = Field(gt=0)
    rural: bool
    source_id: str


class Therapy(BaseModel):
    therapy_id: str
    name: str
    indication: str
    visit_multiplier: int = Field(ge=1)
    source_id: str


class Center(BaseModel):
    center_id: str
    name: str
    state: str
    source_id: str


class MedicaidCoverage(BaseModel):
    state_fips: str
    therapy_id: str
    covered: bool
    source_id: str


class AcsInsurance(BaseModel):
    fips: str
    insured_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    source_id: str


class PrevalenceBound(BaseModel):
    therapy_id: str
    fips: str | None
    prev_low_per_100k: float = Field(gt=0)
    prev_high_per_100k: float = Field(gt=0)
    source_id: str


class Distance(BaseModel):
    fips: str
    therapy_id: str
    one_way_miles: float = Field(ge=0)
    nearest_center_id: str
    source_id: str


class Capacity(BaseModel):
    center_id: str
    slots_per_month: int = Field(ge=0)
    source_id: str


class CountyTherapy(BaseModel):
    fips: str
    therapy_id: str
    role: str
    path_exercised: str
    why_present: str
    expected_behavior: str


class Interval(BaseModel):
    """Closed interval. Harnesses never collapse this to a silent point."""

    low: float
    high: float

    @property
    def ratio(self) -> float:
        if self.low <= 0:
            return float("inf")
        return self.high / self.low

    def midpoint_explicit(self) -> float:
        """Display-only. Callers must opt in; never the stored estimate."""

        return (self.low + self.high) / 2.0


class WeightScheme(BaseModel):
    name: str
    travel: float = Field(ge=0.0, le=1.0)
    medicaid: float = Field(ge=0.0, le=1.0)
    insurance: float = Field(ge=0.0, le=1.0)
    capacity: float = Field(ge=0.0, le=1.0)

    def components(self) -> dict[str, float]:
        return {
            "travel": self.travel,
            "medicaid": self.medicaid,
            "insurance": self.insurance,
            "capacity": self.capacity,
        }

    def normalized(self, available: set[str]) -> dict[str, float]:
        raw = {k: v for k, v in self.components().items() if k in available and v > 0}
        total = sum(raw.values())
        if total <= 0:
            return {}
        return {k: v / total for k, v in raw.items()}


class AccessScore(BaseModel):
    fips: str
    therapy_id: str
    scheme: str
    score: float | None
    incomplete: bool
    missing_components: list[str]
    effective_miles: float
    travel_score: float
    medicaid_score: float
    insurance_score: float | None
    capacity_score: float | None
