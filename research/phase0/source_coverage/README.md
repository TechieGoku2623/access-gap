# source_coverage

## What is measured

Per committed source: retrieval freshness against the pinned evaluation
date, county-level completeness, and the missing-data pattern. Queries
run against the DuckDB staging layer.

## Why it decides something

A source with completeness below 0.80, or with silent missingness, is
not usable as a primary index input. Capacity fails that bar on this
slice.

## How to run

```bash
uv run python research/phase0/source_coverage/run.py
```

Not a live CMS or Census pull.
