# Phase 0 harnesses

`make research` runs these in order:

1. `source_coverage/run.py` — freshness, completeness, missingness per source
2. `index_sensitivity/run.py` — rank correlation across weight schemes
3. `prevalence_bounds/run.py` — interval width; never a silent point estimate
4. `render_docs.py` — write `docs/phase-0/research-memo.md`, `docs/EVALUATION.md`, and the measured tables in `README.md`

No number in the memo is typed by hand. If a quantity cannot be produced here, the memo says **unmeasured** and names the measurement that would settle it.
