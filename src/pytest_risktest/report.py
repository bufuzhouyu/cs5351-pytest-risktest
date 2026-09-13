"""Run reports: machine-readable JSON, human-readable Markdown and standalone HTML."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


def write_json(path: Path | str, payload: Mapping[str, object]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return target


def read_json(path: Path | str) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _fmt(value: object, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def summary_table(payload: Mapping[str, object]) -> str:
    """Render the top-level numbers of a run report as a Markdown table."""
    keys = [
        "policy",
        "granularity",
        "total_tests",
        "selected",
        "deselected",
        "skip_rate",
        "failed",
        "duration_s",
        "monitor_overhead_pct",
    ]
    lines = ["| metric | value |", "| --- | --- |"]
    for key in keys:
        if key in payload:
            lines.append(f"| {key} | {_fmt(payload[key])} |")
    return "\n".join(lines)


def render_markdown(payload: Mapping[str, object]) -> str:
    lines = ["# pytest-risktest run report", ""]
    lines.append(summary_table(payload))
    reasons = payload.get("reason_histogram") or {}
    if reasons:
        lines += ["", "## Why tests were selected", "", "| reason | tests |", "| --- | --- |"]
        for reason, count in sorted(reasons.items()):  # type: ignore[union-attr]
            lines.append(f"| {reason} | {count} |")
    changed = payload.get("changed_files") or []
    if changed:
        lines += ["", "## Changed files", ""]
        lines += [f"- `{path}`" for path in changed]  # type: ignore[union-attr]
    failures = payload.get("failures") or []
    lines += ["", "## Failing tests", ""]
    if failures:
        lines += [f"- `{nodeid}`" for nodeid in failures]  # type: ignore[union-attr]
    else:
        lines.append("- none")
    findings = payload.get("flaky_findings") or {}
    if findings:
        lines += ["", "## Flakiness findings", "", "| test | verdict |", "| --- | --- |"]
        for nodeid, verdict in sorted(findings.items()):  # type: ignore[union-attr]
            lines.append(f"| `{nodeid}` | {verdict} |")
    return "\n".join(lines) + "\n"


def svg_bar_chart(
    data: Mapping[str, float],
    *,
    title: str = "",
    width: int = 640,
    height: int = 320,
    bar_color: str = "#2b6cb0",
    value_format: str = "{:.2f}",
) -> str:
    """Return a self-contained SVG bar chart (no third-party plotting library)."""
    if not data:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"></svg>'
    pad_left, pad_right, pad_top, pad_bottom = 48, 16, 36, 72
    plot_width = width - pad_left - pad_right
    plot_height = height - pad_top - pad_bottom
    maximum = max(abs(value) for value in data.values()) or 1.0
    slot = plot_width / max(len(data), 1)
    bar_width = slot * 0.6
    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Segoe UI, Arial, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    if title:
        parts.append(
            f'<text x="{width / 2:.0f}" y="20" text-anchor="middle" font-size="14" '
            f'font-weight="600" fill="#1a202c">{html.escape(title)}</text>'
        )
    parts.append(
        f'<line x1="{pad_left}" y1="{pad_top + plot_height}" x2="{pad_left + plot_width}" '
        f'y2="{pad_top + plot_height}" stroke="#a0aec0" stroke-width="1"/>'
    )
    for index, (label, value) in enumerate(data.items()):
        bar_height = abs(value) / maximum * plot_height
        x = pad_left + index * slot + (slot - bar_width) / 2
        y = pad_top + plot_height - bar_height
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" '
            f'fill="{bar_color}" rx="2"/>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" '
            f'font-size="11" fill="#2d3748">{html.escape(value_format.format(value))}</text>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{pad_top + plot_height + 16:.1f}" '
            f'text-anchor="end" font-size="11" fill="#4a5568" '
            f'transform="rotate(-35 {x + bar_width / 2:.1f} {pad_top + plot_height + 16:.1f})">'
            f"{html.escape(label)}</text>"
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_html(payload: Mapping[str, object]) -> str:
    reasons = {str(k): float(v) for k, v in (payload.get("reason_histogram") or {}).items()}  # type: ignore[union-attr]
    chart = svg_bar_chart(reasons, title="Selected tests by reason")
    failures = payload.get("failures") or []
    rows = "\n".join(
        f"<tr><td><code>{html.escape(str(nodeid))}</code></td></tr>" for nodeid in failures  # type: ignore[union-attr]
    ) or '<tr><td class="muted">none</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>pytest-risktest report</title>
<style>
 body {{ font-family: "Segoe UI", Arial, sans-serif; margin: 2rem auto; max-width: 900px; color:#1a202c; }}
 table {{ border-collapse: collapse; width: 100%; margin: .5rem 0 1.5rem; }}
 th, td {{ border: 1px solid #e2e8f0; padding: .4rem .6rem; text-align: left; font-size: .92rem; }}
 th {{ background: #f7fafc; }}
 code {{ background: #f1f5f9; padding: .1rem .3rem; border-radius: 3px; }}
 .muted {{ color: #718096; }}
</style>
</head>
<body>
<h1>pytest-risktest run report</h1>
<pre>{html.escape(summary_table(payload))}</pre>
<h2>Selection reasons</h2>
{chart}
<h2>Failing tests</h2>
<table><thead><tr><th>test</th></tr></thead><tbody>{rows}</tbody></table>
</body>
</html>
"""


def write_html(path: Path | str, payload: Mapping[str, object]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_html(payload), encoding="utf-8")
    return target


def write_markdown(path: Path | str, payload: Mapping[str, object]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(payload), encoding="utf-8")
    return target


def markdown_table(rows: Sequence[Mapping[str, object]], columns: Optional[Sequence[str]] = None) -> str:
    """Generic Markdown table renderer used by the benchmark harness."""
    if not rows:
        return ""
    columns = list(columns or rows[0].keys())
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines) + "\n"

