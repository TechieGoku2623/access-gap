# Data

Phase 0 does not call CMS, Census, or manufacturer APIs. The committed
objects are a 3-state county × therapy slice:

- `data/sample/manifests/sources.json` — source id, URL, retrieval date
  (2026-01-15), license note
- `data/sample/counties.csv` — 12 counties in CA, TX, WV (real FIPS,
  designed populations)
- `data/sample/therapies.csv` — Zolgensma, Casgevy, Luxturna plus
  multi-visit multipliers
- `data/sample/centers.csv`, `distances.csv`, `medicaid_coverage.csv`,
  `acs_insurance.csv`, `prevalence.csv`, `capacity.csv`
- `data/sample/county_therapy.csv` — 36-row analytical grain, five
  designed roles

Every numeric column traces to a `source_id` in the manifest. Gilmer
County ACS `insured_pct` is blank on purpose.

**Do not commit a live national extract to git.** `data/*` is gitignored
except `data/sample/`. Later phases write a manifest (source URL,
retrieval timestamp, row count, sha256) and keep raw files in gitignored
bronze storage.

No application is required to run Phase 0. A later CMS
research-identifiable file would need a DUA; that path is out of scope
until Phase 2 names it.
