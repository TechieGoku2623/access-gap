"""access-gap: county × therapy access to approved gene therapies.

Analytical research tooling. Not a care navigator, not a coverage
determination, and not medical advice.
"""

__version__ = "0.1.0"

SAFETY_DISCLAIMER = (
    "Research tool only. Designed stand-in numbers, not a live CMS or Census "
    "pull. This is not a care navigator and not a coverage determination."
)

# Pinned so freshness math is deterministic in CI.
EVAL_DATE = "2026-10-06"
COMPLETENESS_THRESHOLD = 0.80
SPEARMAN_THRESHOLD = 0.70
WIDE_PREVALENCE_RATIO = 10.0
