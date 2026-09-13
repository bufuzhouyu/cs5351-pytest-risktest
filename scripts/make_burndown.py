"""Render ``docs/process/burndown.csv`` into ``docs/report/figures/burndown.svg``.

The chart shows the planned (ideal) line for every sprint week and the actual
line for the weeks where the team has recorded data.  Weeks without actuals stay
empty on purpose: the burndown is project evidence, and an invented line would be
a false artefact.

Usage::

    python scripts/make_burndown.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "docs" / "process" / "burndown.csv"
OUTPUT = ROOT / "docs" / "report" / "figures" / "burndown.svg"

WIDTH, HEIGHT = 720, 360
PAD_LEFT, PAD_RIGHT, PAD_TOP, PAD_BOTTOM = 60, 20, 40, 60


def load_rows() -> list[dict]:
    rows = []
    with CSV_PATH.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["week"] = int(row["week"])
            row["planned_remaining"] = float(row["planned_remaining"])
            raw = (row.get("actual_remaining") or "").strip()
            row["actual_remaining"] = float(raw) if raw else None
            rows.append(row)
    return rows


def main() -> int:
    rows = load_rows()
    weeks = [row["week"] for row in rows]
    first_week, last_week = min(weeks), max(weeks)
    max_points = max(row["planned_remaining"] for row in rows) or 1.0
    plot_width = WIDTH - PAD_LEFT - PAD_RIGHT
    plot_height = HEIGHT - PAD_TOP - PAD_BOTTOM

    def x(week: int) -> float:
        span = max(last_week - first_week, 1)
        return PAD_LEFT + (week - first_week) / span * plot_width

    def y(points: float) -> float:
        return PAD_TOP + plot_height - points / max_points * plot_height

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"'
        ' font-family="Segoe UI, Arial, sans-serif">' % (WIDTH, HEIGHT, WIDTH, HEIGHT),
        '<rect width="%d" height="%d" fill="#ffffff"/>' % (WIDTH, HEIGHT),
        '<text x="%d" y="22" text-anchor="middle" font-size="15" font-weight="600"'
        ' fill="#1a202c">Burndown (story points)</text>' % (WIDTH // 2),
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#a0aec0"/>'
        % (PAD_LEFT, PAD_TOP + plot_height, PAD_LEFT + plot_width, PAD_TOP + plot_height),
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#a0aec0"/>'
        % (PAD_LEFT, PAD_TOP, PAD_LEFT, PAD_TOP + plot_height),
    ]
    for fraction in (0.25, 0.5, 0.75, 1.0):
        value = max_points * fraction
        parts.append(
            '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#edf2f7"/>'
            % (PAD_LEFT, y(value), PAD_LEFT + plot_width, y(value))
        )
        parts.append(
            '<text x="%d" y="%.1f" text-anchor="end" font-size="11" fill="#4a5568">%.0f</text>'
            % (PAD_LEFT - 8, y(value) + 4, value)
        )
    planned = " ".join(
        "%.1f,%.1f" % (x(row["week"]), y(row["planned_remaining"])) for row in rows
    )
    parts.append(
        '<polyline points="%s" fill="none" stroke="#a0aec0" stroke-dasharray="5 4"/>' % planned
    )
    actual_points = [
        (x(row["week"]), y(row["actual_remaining"]))
        for row in rows
        if row["actual_remaining"] is not None
    ]
    if actual_points:
        points = " ".join("%.1f,%.1f" % point for point in actual_points)
        parts.append(
            '<polyline points="%s" fill="none" stroke="#2b6cb0" stroke-width="2"/>' % points
        )
        for px, py in actual_points:
            parts.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="#2b6cb0"/>' % (px, py))
    for row in rows:
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="10" fill="#4a5568">%d</text>'
            % (x(row["week"]), PAD_TOP + plot_height + 18, row["week"])
        )
    parts.append(
        '<text x="%.1f" y="%d" text-anchor="middle" font-size="11" fill="#4a5568">'
        'project week</text>' % (PAD_LEFT + plot_width / 2, HEIGHT - 12)
    )
    parts.append(
        '<rect x="%d" y="%d" width="12" height="3" fill="#a0aec0"/>'
        '<text x="%d" y="%d" font-size="11" fill="#4a5568">planned</text>'
        % (WIDTH - 190, PAD_TOP - 8, WIDTH - 172, PAD_TOP - 3)
    )
    parts.append(
        '<rect x="%d" y="%d" width="12" height="3" fill="#2b6cb0"/>'
        '<text x="%d" y="%d" font-size="11" fill="#4a5568">actual</text>'
        % (WIDTH - 110, PAD_TOP - 8, WIDTH - 92, PAD_TOP - 3)
    )
    parts.append("</svg>")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")
    recorded = sum(1 for row in rows if row["actual_remaining"] is not None)
    print("%s written (%d weeks with actual data)" % (OUTPUT, recorded))
    print("Weeks without actual data stay empty; update docs/process/burndown.csv weekly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

