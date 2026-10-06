# index_sensitivity

## What is measured

Spearman rank correlation of the county × therapy access index across
five explicit weight schemes. Incomplete rows (missing ACS) are scored
with renormalized weights and flagged; they are dropped from pairwise
rank correlation so missingness is not imputed to zero.

## Why it decides something

If the minimum pairwise Spearman is below 0.70, rankings swing with
defensible weight choices and the composite index needs rethinking.

## How to run

```bash
uv run python research/phase0/index_sensitivity/run.py
```
