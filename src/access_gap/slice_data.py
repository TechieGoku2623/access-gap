"""Load the committed 3-state slice. No live CMS or Census pull."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pydantic import BaseModel, Field

from access_gap.config import get_settings
from access_gap.schemas import (
    AcsInsurance,
    Capacity,
    Center,
    County,
    CountyTherapy,
    Distance,
    MedicaidCoverage,
    PrevalenceBound,
    SourceManifest,
    Therapy,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _opt_float(raw: str) -> float | None:
    text = raw.strip()
    if text == "":
        return None
    return float(text)


def _opt_str(raw: str) -> str | None:
    text = raw.strip()
    if text == "":
        return None
    return text


class Slice(BaseModel):
    sources: list[SourceManifest]
    counties: list[County]
    therapies: list[Therapy]
    centers: list[Center]
    coverage_rows: list[MedicaidCoverage] = Field(alias="coverage")
    insurance_rows: list[AcsInsurance] = Field(alias="insurance")
    prevalence_rows: list[PrevalenceBound] = Field(alias="prevalence")
    distances: list[Distance]
    capacities: list[Capacity]
    pairs: list[CountyTherapy]

    model_config = {"populate_by_name": True}

    def county(self, fips: str) -> County:
        for row in self.counties:
            if row.fips == fips:
                return row
        raise KeyError(fips)

    def therapy(self, therapy_id: str) -> Therapy:
        for row in self.therapies:
            if row.therapy_id == therapy_id:
                return row
        raise KeyError(therapy_id)

    def coverage(self, state_fips: str, therapy_id: str) -> MedicaidCoverage:
        for row in self.coverage_rows:
            if row.state_fips == state_fips and row.therapy_id == therapy_id:
                return row
        raise KeyError((state_fips, therapy_id))

    def insurance(self, fips: str) -> AcsInsurance:
        for row in self.insurance_rows:
            if row.fips == fips:
                return row
        raise KeyError(fips)

    def distance(self, fips: str, therapy_id: str) -> Distance:
        for row in self.distances:
            if row.fips == fips and row.therapy_id == therapy_id:
                return row
        raise KeyError((fips, therapy_id))

    def prevalence(self, fips: str, therapy_id: str) -> PrevalenceBound:
        specific = [
            row for row in self.prevalence_rows if row.therapy_id == therapy_id and row.fips == fips
        ]
        if specific:
            return specific[0]
        general = [
            row for row in self.prevalence_rows if row.therapy_id == therapy_id and row.fips is None
        ]
        if general:
            return general[0]
        raise KeyError((fips, therapy_id))

    def capacity_for(self, center_id: str) -> Capacity | None:
        for row in self.capacities:
            if row.center_id == center_id:
                return row
        return None

    def designed_pairs(self) -> list[CountyTherapy]:
        return [p for p in self.pairs if p.role != "filler"]

    def source(self, source_id: str) -> SourceManifest:
        for row in self.sources:
            if row.id == source_id:
                return row
        raise KeyError(source_id)


def load_slice(sample_dir: Path | None = None) -> Slice:
    root = sample_dir or get_settings().sample_dir
    raw_sources = json.loads((root / "manifests" / "sources.json").read_text(encoding="utf-8"))
    sources = [SourceManifest.model_validate(item) for item in raw_sources["sources"]]
    counties = [
        County.model_validate(_coerce_county(row)) for row in _read_csv(root / "counties.csv")
    ]
    therapies = [
        Therapy.model_validate(_coerce_therapy(row)) for row in _read_csv(root / "therapies.csv")
    ]
    centers = [Center.model_validate(row) for row in _read_csv(root / "centers.csv")]
    coverage = [
        MedicaidCoverage.model_validate(_coerce_coverage(row))
        for row in _read_csv(root / "medicaid_coverage.csv")
    ]
    insurance = [
        AcsInsurance.model_validate(_coerce_insurance(row))
        for row in _read_csv(root / "acs_insurance.csv")
    ]
    prevalence = [
        PrevalenceBound.model_validate(_coerce_prev(row))
        for row in _read_csv(root / "prevalence.csv")
    ]
    distances = [
        Distance.model_validate(_coerce_distance(row)) for row in _read_csv(root / "distances.csv")
    ]
    capacities = [
        Capacity.model_validate(_coerce_capacity(row)) for row in _read_csv(root / "capacity.csv")
    ]
    pairs = [CountyTherapy.model_validate(row) for row in _read_csv(root / "county_therapy.csv")]
    return Slice(
        sources=sources,
        counties=counties,
        therapies=therapies,
        centers=centers,
        coverage=coverage,
        insurance=insurance,
        prevalence=prevalence,
        distances=distances,
        capacities=capacities,
        pairs=pairs,
    )


def _coerce_county(row: dict[str, str]) -> dict[str, object]:
    return {
        **row,
        "population": int(row["population"]),
        "rural": row["rural"].strip().lower() in {"1", "true", "yes"},
    }


def _coerce_therapy(row: dict[str, str]) -> dict[str, object]:
    return {**row, "visit_multiplier": int(row["visit_multiplier"])}


def _coerce_coverage(row: dict[str, str]) -> dict[str, object]:
    return {**row, "covered": row["covered"].strip().lower() in {"1", "true", "yes"}}


def _coerce_insurance(row: dict[str, str]) -> dict[str, object]:
    return {**row, "insured_pct": _opt_float(row["insured_pct"])}


def _coerce_prev(row: dict[str, str]) -> dict[str, object]:
    return {
        **row,
        "fips": _opt_str(row["fips"]),
        "prev_low_per_100k": float(row["prev_low_per_100k"]),
        "prev_high_per_100k": float(row["prev_high_per_100k"]),
    }


def _coerce_distance(row: dict[str, str]) -> dict[str, object]:
    return {**row, "one_way_miles": float(row["one_way_miles"])}


def _coerce_capacity(row: dict[str, str]) -> dict[str, object]:
    return {**row, "slots_per_month": int(row["slots_per_month"])}
