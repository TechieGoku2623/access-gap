# prevalence_bounds

## What is measured

Width of published prevalence ranges per therapy, plus the county ×
therapy eligible-population interval. Intervals are propagated. A
midpoint is never stored as the estimate.

## Why it decides something

A 10× prevalence range makes eligible population an interval. Using a
silent point estimate would invent patients.

## How to run

```bash
uv run python research/phase0/prevalence_bounds/run.py
```
