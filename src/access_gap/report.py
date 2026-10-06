"""County choropleth HTML from the committed 3-state slice. No live GIS."""

from __future__ import annotations

from pathlib import Path

from access_gap.index import score_row
from access_gap.slice_data import Slice, load_slice
from access_gap.weights import SCHEMES

# Schematic positions — not a projection. Enough to see CA / TX / WV clusters.
LAYOUT: dict[str, tuple[float, float, float, float]] = {
    "06075": (40, 80, 70, 36),
    "06001": (40, 130, 70, 36),
    "06037": (40, 180, 70, 36),
    "06049": (40, 230, 70, 36),
    "48201": (220, 80, 70, 36),
    "48029": (220, 130, 70, 36),
    "48453": (220, 180, 70, 36),
    "48105": (220, 230, 70, 36),
    "54039": (400, 80, 70, 36),
    "54047": (400, 130, 70, 36),
    "54021": (400, 180, 70, 36),
    "54013": (400, 230, 70, 36),
}


def _color(score: float | None, incomplete: bool) -> str:
    if score is None:
        return "#9ca3af"
    # Transparent sequential scale: low access = rust, high = teal.
    t = max(0.0, min(1.0, score))
    r = int(180 * (1 - t) + 15 * t)
    g = int(70 * (1 - t) + 140 * t)
    b = int(50 * (1 - t) + 130 * t)
    if incomplete:
        return f"rgb({r},{g},{b})"
    return f"rgb({r},{g},{b})"


def choropleth_html(
    slice_: Slice | None = None,
    *,
    therapy_id: str = "zolgensma",
) -> str:
    data = slice_ or load_slice()
    scheme = SCHEMES["default"]
    cells: list[str] = []
    legend_rows: list[str] = []
    for pair in data.pairs:
        if pair.therapy_id != therapy_id:
            continue
        scored = score_row(data, pair, scheme)
        county = data.county(pair.fips)
        x, y, w, h = LAYOUT[pair.fips]
        fill = _color(scored.score, scored.incomplete)
        label = f"{county.name.split()[0]}"
        score_txt = "—" if scored.score is None else f"{scored.score:.2f}"
        extra = (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#miss)" />'
            if scored.incomplete
            else ""
        )
        cells.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="#111" stroke-width="1.2" rx="4" />{extra}'
            f'<text x="{x + 6}" y="{y + 15}" font-size="10" font-family="ui-monospace,monospace">'
            f"{pair.fips}</text>"
            f'<text x="{x + 6}" y="{y + 28}" font-size="9" font-family="ui-sans-serif,sans-serif">'
            f"{label} {score_txt}</text>"
        )
        miss = " ACS missing" if scored.incomplete else ""
        legend_rows.append(
            f"<tr><td>{pair.fips}</td><td>{county.name}</td><td>{county.state}</td>"
            f"<td>{'rural' if county.rural else 'urban'}</td>"
            f"<td>{score_txt}</td><td>{miss or 'complete'}</td></tr>"
        )
    svg_cells = "\n".join(cells)
    table = "\n".join(legend_rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>access-gap choropleth — {therapy_id}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; max-width: 960px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
    th, td {{ border-bottom: 1px solid #ddd; text-align: left; padding: 0.35rem 0.5rem; }}
    .note {{ color: #444; max-width: 40rem; }}
  </style>
</head>
<body>
  <h1>access-gap county index — {therapy_id}</h1>
  <p class="note">
    Designed 3-state stand-in. Not a live CMS or Census pull. Not a care navigator.
    Color is the <strong>default</strong> scheme (travel 0.40, medicaid 0.35, insurance 0.25).
    Hatched counties have missing ACS; the index does <strong>not</strong> impute zero.
    Eligible population is an interval and is not drawn as a point.
  </p>
  <svg viewBox="0 0 520 300" width="720" height="420" role="img"
       aria-label="Schematic county map of the sample slice">
    <pattern id="miss" width="6" height="6" patternUnits="userSpaceOnUse">
      <path d="M0,6 L6,0" stroke="#111" stroke-width="0.6" opacity="0.35"/>
    </pattern>
    <text x="40" y="28" font-size="14">California</text>
    <text x="220" y="28" font-size="14">Texas</text>
    <text x="400" y="28" font-size="14">West Virginia</text>
    {svg_cells}
  </svg>
  <h2>County table</h2>
  <table>
    <thead><tr><th>FIPS</th><th>County</th><th>State</th><th>Rural</th><th>Index</th><th>ACS</th></tr></thead>
    <tbody>
      {table}
    </tbody>
  </table>
</body>
</html>
"""


def write_report(dest: Path, *, therapy_id: str = "zolgensma") -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(choropleth_html(therapy_id=therapy_id), encoding="utf-8")
    return dest
