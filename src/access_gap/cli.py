"""Phase 0 CLI. Scoring APIs are Phase 2."""

from __future__ import annotations

import typer
from rich.console import Console

from access_gap import SAFETY_DISCLAIMER, __version__
from access_gap.config import get_settings
from access_gap.logging import configure_logging
from access_gap.slice_data import load_slice

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=140)


@app.callback()
def _main() -> None:
    configure_logging()


@app.command("version")
def version() -> None:
    """Print the package version."""

    console.print(f"access-gap {__version__}")


@app.command("demo-plan")
def demo_plan(
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Print the five designed county × therapy cases and the path each exercises."""

    slice_ = load_slice()
    console.print("[bold]access-gap designed county × therapy cases[/bold]\n")
    for pair in slice_.designed_pairs():
        county = slice_.county(pair.fips)
        therapy = slice_.therapy(pair.therapy_id)
        console.print(
            f"[bold]{pair.role}[/bold]  {county.fips} {county.name}, {county.state}  "
            f"× {therapy.therapy_id}"
        )
        console.print(f"  path:     {pair.path_exercised}")
        console.print(f"  expected: {pair.expected_behavior}\n")
    console.print()
    console.print(SAFETY_DISCLAIMER)
    if dry_run:
        console.print(
            "\nDry run only. Scoring (`access-gap score`) is Phase 2; "
            "this command exists so `make demo` can show that the slice "
            "is designed, not sampled from a live CMS pull."
        )
    console.print(f"Sample directory: {get_settings().sample_dir}")


@app.command("sample-path")
def sample_path() -> None:
    """Print the committed sample directory path."""

    console.print(str(get_settings().sample_dir.resolve()))
