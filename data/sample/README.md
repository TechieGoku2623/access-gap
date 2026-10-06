# Sample data

This is a **committed 3-state slice** (California, Texas, West Virginia).
Values are designed stand-ins. They are not a live CMS, Census ACS, or
manufacturer-center pull. Every number traces to a source id with a
retrieval date in `manifests/sources.json` (retrieved 2026-01-15).

FIPS codes are real. Populations, miles, coverage bits, and prevalence
ranges are designed so the five walkthrough cases exist. Do not quote
them as official statistics.

| Role | FIPS | Therapy | Why it is here |
| --- | --- | --- | --- |
| best_case | 06075 San Francisco | zolgensma | Adjacent to a certified center; Medicaid covers. |
| distance_dominated | 48105 Crockett | zolgensma | 360 one-way miles. Multi-visit burden dominates. |
| coverage_gap | 48201 Harris | casgevy | 14 miles from a center; Medicaid does not cover. |
| wide_prevalence | 54047 McDowell | luxturna | Published prevalence range is 10×. Eligible pop is an interval. |
| missing_acs | 54021 Gilmer | zolgensma | ACS insured_pct is blank. Never impute to zero. |

Analytical unit is county × therapy (36 rows). Travel burden in the
index is `one_way_miles * 2 * visit_multiplier`, not straight-line only.
