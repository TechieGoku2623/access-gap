# index_sensitivity results

Complete-case n = 33. Min Spearman = 0.632. Needs rethinking: True.

The composite access index needs rethinking; rankings are not stable across defensible weight schemes (min Spearman 0.632 < 0.70).

| scheme A | scheme B | n | Spearman |
| --- | --- | --- | --- |
| default | equal | 33 | 0.998 |
| default | geography_only | 33 | 0.846 |
| default | coverage_only | 33 | 0.893 |
| default | travel_heavy | 33 | 0.926 |
| equal | geography_only | 33 | 0.835 |
| equal | coverage_only | 33 | 0.905 |
| equal | travel_heavy | 33 | 0.919 |
| geography_only | coverage_only | 33 | 0.632 |
| geography_only | travel_heavy | 33 | 0.955 |
| coverage_only | travel_heavy | 33 | 0.757 |
