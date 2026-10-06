# source_coverage results

Evaluation date 2026-10-06. Counties = 12. County × therapy rows = 36.

Usable: cms_medicaid, acs_s2701, travel_standin, orphanet_cdc, gazetteer, center_list. Not usable as a primary index input: capacity_sparse. ACS missingness on Gilmer is kept as missing.

| source | retrieved | freshness days | n | n missing | completeness | decision |
| --- | --- | --- | --- | --- | --- | --- |
| cms_medicaid | 2026-01-15 | 264 | 9 | 0 | 1.000 | usable |
| acs_s2701 | 2026-01-15 | 264 | 12 | 1 | 0.917 | usable with explicit missing handling (never impute zero) |
| travel_standin | 2026-01-15 | 264 | 36 | 0 | 1.000 | usable |
| orphanet_cdc | 2026-01-15 | 264 | 4 | 0 | 1.000 | usable |
| capacity_sparse | 2026-01-15 | 264 | 2 | 1 | 0.500 | not usable as a primary index input |
| gazetteer | 2026-01-15 | 264 | 12 | 0 | 1.000 | usable |
| center_list | 2026-01-15 | 264 | 3 | 0 | 1.000 | usable |
