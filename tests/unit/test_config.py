from __future__ import annotations

import os

from access_gap.config import get_settings
from access_gap.logging import configure_logging


def test_settings_point_at_committed_sample_dir() -> None:
    settings = get_settings()
    assert (settings.sample_dir / "county_therapy.csv").is_file()
    assert settings.manifest_path.is_file()
    assert (settings.research_dir / "run_all.py").is_file()


def test_configure_logging_does_not_raise() -> None:
    configure_logging()
    os.environ["ACCESS_GAP_ENV"] = "prod"
    try:
        configure_logging()
    finally:
        os.environ.pop("ACCESS_GAP_ENV", None)
    configure_logging()
