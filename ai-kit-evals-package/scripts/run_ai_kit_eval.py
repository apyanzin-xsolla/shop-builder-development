#!/usr/bin/env python3
"""Reusable AI Kit eval runner.

No external dependencies.

Outputs:
- Markdown report
- scored JSON
- Mini Apps dashboard data JSON
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


WEIGHTS = {
    "token": 0.30,
    "clarification": 0.25,
    "correction": 0.20,
    "confidence": 0.15,
    "safety": 0.10,
}


def estimate_tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text))


def pct_reduction(baseline: float, ai_kit: float) -> float:
    if baseline <= 0:
        return 0.0 if ai_kit <= 0 else -100.0
    return ((baseline - ai_kit) / baseline) * 100


def validated_confidence(row: dict[str, Any]) -> float:
    if "validated_confidence_rate" in row:
        return float(row["validated_confidence_rate"])
    checklist = float(row.get("skill_checklist_pass_rate", row.get("checklist_pass_rate", 0)))
    sme = float(row.get("sme_review_score", 50))
    sandbox = float(row.get("sandbox_execution_score", 0))
    return round(checklist * 0.70 + sme * 0.20 + sandbox * 0.10, 1)


def normalize_variant(variant: str) -> str:
    if variant == "docs_mcp":
        return "docs"
    return variant


def load_runs(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    rows = payload.get("runs", payload) if isinstance(payload, dict) else payload
    normalized = []
    for row in rows:
        token_value = row.get("total_tokens_to_acceptance")
        if token_value is None:
            token_value = estimate_tokens(f"{row.get('prompt', '')}\n{row.get('response', '')}")
        case_id = row["case_id"]
        normalized.append(
            {
                "case_id": case_id,
                "case_label": row.get("case_label", case_id),
                "group": row.get("group", "production" if case_id.startswith("prod_") else "prompt_only"),
                "variant": normalize_variant(row["variant"]),
                "tokens": int(token_value),
                "clarification_turns": int(row.get("clarification_turns", 0)),
                "manual_corrections": int(row.get("manual_corrections", 0)),
                "skill_checklist_pass_rate": float(
                    row.get("skill_checklist_pass_rate", row.get("checklist_pass_rate", 0))
                ),
                "validated_confidence_rate": validated_confidence(row),
                "safety_errors": int(row.get("safety_errors", 0)),
            }
        )
    return metadata, normalized


def by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["case_id"], {})[row["variant"]] = row
    return grouped


def compare(ai: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    token = pct_reduction(baseline["tokens"], ai["tokens"])
    clarification = pct_reduction(baseline["clarification_turns"], ai["clarification_turns"])
    correction = pct_reduction(baseline["manual_corrections"], ai["manual_corrections"])
    confidence = ai["validated_confidence_rate"] - baseline["validated_confidence_rate"]
    safety = pct_reduction(baseline["safety_errors"], ai["safety_errors"])
    gain = (
        token * WEIGHTS["token"]
        + clarification * WEIGHTS["clarification"]
        + correction * WEIGHTS["correction"]
        + confidence * WEIGHTS["confidence"]
        + safety * WEIGHTS["safety"]
    )
    return {
        "case_id": ai["case_id"],
        "case_label": ai["case_label"],
        "group": ai["group"],
        "baseline": baseline["variant"],
        "ai_tokens": ai["tokens"],
        "baseline_tokens": baseline["tokens"],
        "token_reduction_pct": round(token, 1),
        "ai_clarifications": ai["clarification_turns"],
        "baseline_clarifications": baseline["clarification_turns"],
        "ai_corrections": ai["manual_corrections"],
        "baseline_corrections": baseline["manual_corrections"],
        "ai_skill_checklist": ai["skill_checklist_pass_rate"],
        "baseline_skill_checklist": baseline["skill_checklist_pass_rate"],
        "ai_validated_confidence": ai["validated_confidence_rate"],
        "baseline_validated_confidence": baseline["validated_confidence_rate"],
        "ai_safety_errors": ai["safety_errors"],
        "baseline_safety_errors": baseline["safety_errors"],
        "efficiency_gain": round(gain, 1),
        "decision": decision(gain, ai["safety_errors"]),
    }


def decision(gain: float, safety_errors: int) -> str:
    if safety_errors > 0:
        return "Do not use: safety error"
    if gain >= 25:
        return "Use AI Kit"
    if gain >= 10:
        return "Use with improvements"
    if gain >= 0:
        return "Weak value"
    return "Do not use"


def score(rows: list[dict[str, Any]], baselines: list[str]) -> list[dict[str, Any]]:
    scored = []
    for variants in by_case(rows).values():
        ai = variants.get("ai_kit")
        if not ai:
            continue
        for baseline_name in baselines:
            baseline = variants.get(baseline_name)
            if baseline:
                scored.append(compare(ai, baseline))
    return scored


def aggregate(scored: list[dict[str, Any]]) -> dict[str, Any]:
    if not scored:
        return {"avg_efficiency_gain_pct": 0, "token_reduction_pct": 0}
    ai_tokens = sum(row["ai_tokens"] for row in scored)
    baseline_tokens = sum(row["baseline_tokens"] for row in scored)
    return {
        "avg_efficiency_gain_pct": round(sum(row["efficiency_gain"] for row in scored) / len(scored), 1),
        "ai_tokens": ai_tokens,
        "baseline_tokens": baseline_tokens,
        "token_reduction_pct": round(pct_reduction(baseline_tokens, ai_tokens), 1),
    }


def render_report(scored: list[dict[str, Any]]) -> str:
    lines = [
        "# AI Kit Eval Report",
        "",
        "| Case | Baseline | AI tokens | Baseline tokens | Token reduction | Validated confidence AI/Baseline | Safety AI/Baseline | Gain | Decision |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in scored:
        lines.append(
            f"| {row['case_label']} | {row['baseline']} | {row['ai_tokens']:,} | {row['baseline_tokens']:,} | {row['token_reduction_pct']}% | {row['ai_validated_confidence']}% / {row['baseline_validated_confidence']}% | {row['ai_safety_errors']} / {row['baseline_safety_errors']} | {row['efficiency_gain']}% | {row['decision']} |"
        )
    agg = aggregate(scored)
    lines += [
        "",
        "## Aggregate",
        "",
        f"- Average efficiency gain: `{agg['avg_efficiency_gain_pct']}%`",
        f"- Token reduction: `{agg['token_reduction_pct']}%`",
        "",
        "Notes:",
        "- `Validated confidence` is not raw checklist coverage.",
        "- Use provider token telemetry when available; otherwise deterministic estimates are OK for pilot runs.",
    ]
    return "\n".join(lines) + "\n"


def dashboard_data(metadata: dict[str, Any], rows: list[dict[str, Any]], scored: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = [row for row in rows if row["group"] == "prompt_only"]
    production = [row for row in rows if row["group"] == "production"]
    prompt_ai = [row for row in prompt if row["variant"] == "ai_kit"]
    prompt_no = [row for row in prompt if row["variant"] == "no_context"]
    prod_ai = [row for row in production if row["variant"] == "ai_kit"]
    prod_docs = [row for row in production if row["variant"] == "docs"]
    prod_no = [row for row in production if row["variant"] == "no_context"]
    return {
        "metadata": metadata,
        "aggregate": aggregate(scored),
        "prompt_only": {
            "cases": [row["case_label"] for row in prompt_ai],
            "ai_kit_tokens": [row["tokens"] for row in prompt_ai],
            "no_context_tokens": [row["tokens"] for row in prompt_no],
            "ai_kit_validated_confidence_pct": [row["validated_confidence_rate"] for row in prompt_ai],
            "no_context_validated_confidence_pct": [row["validated_confidence_rate"] for row in prompt_no],
        },
        "production": {
            "cases": [row["case_label"] for row in prod_ai],
            "ai_kit_tokens": [row["tokens"] for row in prod_ai],
            "docs_tokens": [row["tokens"] for row in prod_docs],
            "no_context_tokens": [row["tokens"] for row in prod_no],
            "ai_kit_validated_confidence_pct": [row["validated_confidence_rate"] for row in prod_ai],
            "docs_validated_confidence_pct": [row["validated_confidence_rate"] for row in prod_docs],
            "no_context_validated_confidence_pct": [row["validated_confidence_rate"] for row in prod_no],
            "clarifications": [
                sum(row["clarification_turns"] for row in prod_ai),
                sum(row["clarification_turns"] for row in prod_docs),
                sum(row["clarification_turns"] for row in prod_no),
            ],
            "manual_corrections": [
                sum(row["manual_corrections"] for row in prod_ai),
                sum(row["manual_corrections"] for row in prod_docs),
                sum(row["manual_corrections"] for row in prod_no),
            ],
            "safety_errors": [
                sum(row["safety_errors"] for row in prod_ai),
                sum(row["safety_errors"] for row in prod_docs),
                sum(row["safety_errors"] for row in prod_no),
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI Kit eval scoring.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("eval-output"))
    parser.add_argument("--baselines", default="docs,no_context")
    args = parser.parse_args()

    metadata, rows = load_runs(args.input)
    baselines = [item.strip() for item in args.baselines.split(",") if item.strip()]
    scored = score(rows, baselines)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "ai-kit-eval-report.md").write_text(render_report(scored), encoding="utf-8")
    (args.out_dir / "ai-kit-eval-score.json").write_text(json.dumps(scored, indent=2), encoding="utf-8")
    (args.out_dir / "dashboard-data.json").write_text(
        json.dumps(dashboard_data(metadata, rows, scored), indent=2),
        encoding="utf-8",
    )
    print(render_report(scored))
    print(f"Wrote outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
