#!/usr/bin/env python3
"""Generate GitHub-renderable SVG charts for AI Kit evals."""

from __future__ import annotations

import json
from pathlib import Path


COLORS = {
    "ai": "#2fbf8f",
    "docs": "#4f8cff",
    "base": "#d99a21",
    "danger": "#e05d5d",
    "text": "#24292f",
    "muted": "#57606a",
    "grid": "#d8dee4"
}


def bar_chart(title: str, labels: list[str], series: list[tuple[str, list[float], str]], unit: str, ymax: float | None = None) -> str:
    width = 980
    height = 420
    left = 64
    top = 64
    plot_w = width - 120
    plot_h = height - 140
    ymax = ymax or max(max(values) for _, values, _ in series) * 1.15
    group_w = plot_w / len(labels)
    bar_w = min(28, group_w / (len(series) + 1.5))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="34" font-family="Arial" font-size="22" font-weight="700" fill="{COLORS["text"]}">{title}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="{COLORS["grid"]}"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="{COLORS["grid"]}"/>',
    ]

    for tick in range(0, 6):
        value = ymax * tick / 5
        y = top + plot_h - (value / ymax) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="{COLORS["grid"]}" stroke-dasharray="3 3"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 4:.1f}" font-family="Arial" font-size="11" text-anchor="end" fill="{COLORS["muted"]}">{value:.0f}{unit}</text>')

    for i, label in enumerate(labels):
        x0 = left + i * group_w + group_w * 0.18
        parts.append(f'<text x="{left + i * group_w + group_w / 2:.1f}" y="{height - 38}" font-family="Arial" font-size="12" text-anchor="middle" fill="{COLORS["muted"]}">{label}</text>')
        for s_idx, (_name, values, color) in enumerate(series):
            value = values[i]
            bar_h = (value / ymax) * plot_h
            x = x0 + s_idx * (bar_w + 8)
            y = top + plot_h - bar_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{color}"/>')
            parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" font-family="Arial" font-size="10" text-anchor="middle" fill="{COLORS["muted"]}">{value:g}{unit}</text>')

    legend_x = left
    legend_y = height - 16
    for name, _values, color in series:
        parts.append(f'<rect x="{legend_x}" y="{legend_y - 10}" width="10" height="10" fill="{color}" rx="2"/>')
        parts.append(f'<text x="{legend_x + 16}" y="{legend_y}" font-family="Arial" font-size="12" fill="{COLORS["muted"]}">{name}</text>')
        legend_x += 170

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "visualizations" / "dashboard-data.json").read_text(encoding="utf-8"))
    out = root / "visualizations"
    out.mkdir(parents=True, exist_ok=True)

    prompt = data["prompt_only"]
    prod = data["production"]

    (out / "tokens-to-accepted-result.svg").write_text(
        bar_chart(
            "Tokens to accepted result",
            prompt["cases"],
            [
                ("AI Kit", prompt["ai_kit_tokens"], COLORS["ai"]),
                ("No-context baseline", prompt["no_context_tokens"], COLORS["base"]),
            ],
            "t",
        ),
        encoding="utf-8",
    )

    (out / "validated-confidence.svg").write_text(
        bar_chart(
            "Validated confidence",
            prod["cases"],
            [
                ("AI Kit", prod["ai_kit_validated_confidence_pct"], COLORS["ai"]),
                ("Docs baseline", prod["docs_validated_confidence_pct"], COLORS["docs"]),
                ("No-context baseline", prod["no_context_validated_confidence_pct"], COLORS["base"]),
            ],
            "%",
            ymax=100,
        ),
        encoding="utf-8",
    )

    (out / "corrections-and-safety.svg").write_text(
        bar_chart(
            "Corrections and safety errors",
            ["AI Kit", "Docs", "No context"],
            [
                ("Clarifications", prod["clarifications"], COLORS["docs"]),
                ("Manual corrections", prod["manual_corrections"], COLORS["base"]),
                ("Safety errors", prod["safety_errors"], COLORS["danger"]),
            ],
            "",
            ymax=7,
        ),
        encoding="utf-8",
    )

    print("Generated GitHub SVG visualizations.")


if __name__ == "__main__":
    main()
