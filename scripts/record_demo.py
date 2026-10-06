"""Write asciinema v2 casts from real CLI stdout. No credentials."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _cast(path: Path, title: str, sessions: list[tuple[str, int, str]]) -> None:
    header = {
        "version": 2,
        "width": 120,
        "height": 40,
        "timestamp": 0,
        "title": title,
        "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"},
    }
    lines = [json.dumps(header)]
    t = 0.05
    for prompt, code, out in sessions:
        lines.append(json.dumps([t, "o", f"$ {prompt}\r\n"]))
        t += 0.15
        for chunk in out.splitlines(keepends=True):
            text = chunk.replace("\n", "\r\n")
            lines.append(json.dumps([t, "o", text]))
            t += 0.02
        lines.append(json.dumps([t, "o", f"\r\n[exit {code}]\r\n"]))
        t += 0.2
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    cli = [sys.executable, "-m", "access_gap.cli"]
    build = _run([*cli, "demo-build"])
    _cast(DEMO / "01-dbt-build-lineage.cast", "access-gap demo-build", [
        ("make demo-build / access-gap demo-build", *build),
    ])
    c1 = _run([*cli, "county", "--fips", "06075", "--therapy", "zolgensma"])
    c2 = _run([*cli, "county", "--fips", "48105", "--therapy", "zolgensma"])
    c3 = _run([*cli, "county", "--fips", "48201", "--therapy", "casgevy"])
    _cast(
        DEMO / "02-county-decomposition.cast",
        "access-gap county decomposition",
        [
            ("access-gap county --fips 06075 --therapy zolgensma", *c1),
            ("access-gap county --fips 48105 --therapy zolgensma", *c2),
            ("access-gap county --fips 48201 --therapy casgevy", *c3),
        ],
    )
    sens = _run([*cli, "sensitivity", "--therapy", "zolgensma"])
    report = _run([*cli, "report", "--dest", "docs/report.html", "--therapy", "zolgensma"])
    _cast(
        DEMO / "03-sensitivity-and-map.cast",
        "access-gap sensitivity and map",
        [
            ("access-gap sensitivity --therapy zolgensma", *sens),
            ("make report / access-gap report --dest docs/report.html", *report),
        ],
    )
    print(f"wrote casts in {DEMO}")
    if build[0] != 0 or c1[0] != 0 or sens[0] != 0:
        raise SystemExit("expected recording commands to succeed")


if __name__ == "__main__":
    main()
