#!/usr/bin/env python3
"""Score AI Kit eval runs.

Input: JSON with either:

{
  "runs": [
    {
      "case_id": "catalog_design",
      "variant": "ai_kit" | "docs_mcp" | "no_context",
      "total_tokens_to_acceptance": 720,
      "prompt": "...",          # optional, used for token estimate if tokens missing
      "response": "...",        # optional, used for token estimate if tokens missing
      "clarification_turns": 0,
      "manual_corrections": 0,
      "checklist_pass_rate": 100,
      "validated_confidence_rate": 75,
      "safety_errors": 0
    }
  ]
}

or a raw list of the same run objects.

The script compares `ai_kit` to one or more baselines and prints Markdown.
It has no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


WEIGHTS = {
    "token_reduction_pct": 0.30,
    "clarification_reduction_pct": 0.25,
    "manual_correction_reduction_pct": 0.20,
    "checklist_pass_rate_delta": 0.15,
    "safety_error_reduction_pct": 0.10,
}


@dataclass(frozen=True)
class Run:
    case_id: str
    variant: str
    tokens: int
    clarification_turns: int
    manual_corrections: int
    checklist_pass_rate: float
    validated_confidence_rate: float
    safety_errors: int


def estimate_tokens(text: str) -> int:
    """Cheap tokenizer fallback: roughly 4 chars/token for English/code mix."""
    return max(1, round(len(text) / 4))


def as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def load_runs(path: Path) -> list[Run]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw["runs"] if isinstance(raw, dict) and "runs" in raw else raw
    runs: list[Run] = []

    for item in items:
        token_value = item.get("total_tokens_to_acceptance")
        if token_value is None:
            token_value = estimate_tokens(
                f"{item.get('prompt', '')}\n{item.get('response', '')}"
            )

        runs.append(
            Run(
                case_id=str(item["case_id"]),
                variant=str(item["variant"]),
                tokens=as_int(token_value),
                clarification_turns=as_int(item.get("clarification_turns")),
                manual_corrections=as_int(item.get("manual_corrections")),
                checklist_pass_rate=as_float(item.get("checklist_pass_rate")),
                validated_confidence_rate=as_float(
                    item.get("validated_confidence_rate", item.get("checklist_pass_rate"))
                ),
                safety_errors=as_int(item.get("safety_errors")),
            )
        )

    return runs


def pct_reduction(baseline: float, ai_kit: float) -> float:
    if baseline <= 0:
        return 0.0 if ai_kit <= 0 else -100.0
    return ((baseline - ai_kit) / baseline) * 100


def compare(ai: Run, baseline: Run) -> dict[str, Any]:
    token_reduction = pct_reduction(baseline.tokens, ai.tokens)
    clarification_reduction = pct_reduction(
        baseline.clarification_turns, ai.clarification_turns
    )
    correction_reduction = pct_reduction(
        baseline.manual_corrections, ai.manual_corrections
    )
    checklist_delta = ai.validated_confidence_rate - baseline.validated_confidence_rate
    safety_reduction = pct_reduction(baseline.safety_errors, ai.safety_errors)

    efficiency_gain = (
        WEIGHTS["token_reduction_pct"] * token_reduction
        + WEIGHTS["clarification_reduction_pct"] * clarification_reduction
        + WEIGHTS["manual_correction_reduction_pct"] * correction_reduction
        + WEIGHTS["checklist_pass_rate_delta"] * checklist_delta
        + WEIGHTS["safety_error_reduction_pct"] * safety_reduction
    )

    return {
        "case_id": ai.case_id,
        "baseline": baseline.variant,
        "ai_tokens": ai.tokens,
        "baseline_tokens": baseline.tokens,
        "token_reduction_pct": token_reduction,
        "ai_clarifications": ai.clarification_turns,
        "baseline_clarifications": baseline.clarification_turns,
        "ai_corrections": ai.manual_corrections,
        "baseline_corrections": baseline.manual_corrections,
        "ai_checklist": ai.checklist_pass_rate,
        "baseline_checklist": baseline.checklist_pass_rate,
        "ai_validated_confidence": ai.validated_confidence_rate,
        "baseline_validated_confidence": baseline.validated_confidence_rate,
        "ai_safety_errors": ai.safety_errors,
        "baseline_safety_errors": baseline.safety_errors,
        "efficiency_gain": efficiency_gain,
        "decision": decision(efficiency_gain, ai.safety_errors),
    }


def decision(efficiency_gain: float, ai_safety_errors: int) -> str:
    if ai_safety_errors > 0:
        return "Do not use: safety error"
    if efficiency_gain >= 25:
        return "Use AI Kit"
    if efficiency_gain >= 10:
        return "Use with improvements"
    if efficiency_gain >= 0:
        return "Weak value"
    return "Do not use"


def group_by_case(runs: Iterable[Run]) -> dict[str, dict[str, Run]]:
    grouped: dict[str, dict[str, Run]] = {}
    for run in runs:
        grouped.setdefault(run.case_id, {})[run.variant] = run
    return grouped


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def render_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# AI Kit Eval Score",
        "",
        "Formula:",
        "",
        "```text",
        "AI Kit Efficiency Gain =",
        "  0.30 * Token Reduction %",
        "+ 0.25 * Clarification Reduction %",
        "+ 0.20 * Manual Correction Reduction %",
        "+ 0.15 * Validated Confidence Delta",
        "+ 0.10 * Safety Error Reduction %",
        "```",
        "",
        "| Case | Baseline | AI tokens | Baseline tokens | Token reduction | Skill checklist AI/Baseline | Validated confidence AI/Baseline | Safety AI/Baseline | Gain | Decision |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in rows:
        lines.append(
            "| {case_id} | {baseline} | {ai_tokens:,} | {baseline_tokens:,} | {token_reduction} | {ai_checklist:.1f}% / {baseline_checklist:.1f}% | {ai_confidence:.1f}% / {baseline_confidence:.1f}% | {ai_safety_errors} / {baseline_safety_errors} | {gain} | {decision} |".format(
                case_id=row["case_id"],
                baseline=row["baseline"],
                ai_tokens=row["ai_tokens"],
                baseline_tokens=row["baseline_tokens"],
                token_reduction=format_pct(row["token_reduction_pct"]),
                ai_checklist=row["ai_checklist"],
                baseline_checklist=row["baseline_checklist"],
                ai_confidence=row["ai_validated_confidence"],
                baseline_confidence=row["baseline_validated_confidence"],
                ai_safety_errors=row["ai_safety_errors"],
                baseline_safety_errors=row["baseline_safety_errors"],
                gain=format_pct(row["efficiency_gain"]),
                decision=row["decision"],
            )
        )

    if rows:
        avg_gain = sum(row["efficiency_gain"] for row in rows) / len(rows)
        ai_tokens = sum(row["ai_tokens"] for row in rows)
        baseline_tokens = sum(row["baseline_tokens"] for row in rows)
        token_reduction = pct_reduction(baseline_tokens, ai_tokens)
        lines.extend(
            [
                "",
                "## Aggregate",
                "",
                f"- Average efficiency gain: `{avg_gain:.1f}%`",
                f"- AI Kit tokens: `{ai_tokens:,}`",
                f"- Baseline tokens: `{baseline_tokens:,}`",
                f"- Token reduction: `{token_reduction:.1f}%`",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Score AI Kit eval runs.")
    parser.add_argument("input", type=Path, help="Path to eval runs JSON.")
    parser.add_argument(
        "--baseline",
        choices=["no_context", "docs_mcp", "all"],
        default="no_context",
        help="Baseline variant to compare against.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to write scored rows as JSON.",
    )
    args = parser.parse_args()

    grouped = group_by_case(load_runs(args.input))
    rows: list[dict[str, Any]] = []

    for case_id in sorted(grouped):
        variants = grouped[case_id]
        ai = variants.get("ai_kit")
        if not ai:
            continue
        baselines = ["docs_mcp", "no_context"] if args.baseline == "all" else [args.baseline]
        for baseline_name in baselines:
            baseline = variants.get(baseline_name)
            if baseline:
                rows.append(compare(ai, baseline))

    print(render_markdown(rows))

    if args.json_output:
        args.json_output.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
