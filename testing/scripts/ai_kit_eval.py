#!/usr/bin/env python3
"""Run AI Kit eval scoring and generate dashboard artifacts.

This script is designed to be copied into `xsolla-ai-kit` and reused for future
skills. It has no third-party dependencies.

It produces:
- scored JSON
- Markdown report
- dashboard data JSON
- Cursor Canvas dashboard source with the same visualization style used here

Input schema:

{
  "metadata": {
    "title": "Xsolla AI Kit Metrics Dashboard",
    "ready_skills": ["merchant-setup"],
    "excluded_skills": ["login-setup"]
  },
  "runs": [
    {
      "case_id": "merchant_setup",
      "case_label": "Merchant",
      "variant": "ai_kit" | "docs" | "docs_mcp" | "no_context",
      "total_tokens_to_acceptance": 534,
      "prompt": "...",                 // optional token fallback
      "response": "...",               // optional token fallback
      "clarification_turns": 0,
      "manual_corrections": 0,
      "checklist_pass_rate": 100,
      "validated_confidence_rate": 80, // optional
      "sme_review_score": 50,           // optional default for confidence
      "sandbox_execution_score": 0,     // optional default for confidence
      "safety_errors": 0,
      "group": "prompt_only" | "production"
    }
  ]
}
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


WEIGHTS = {
    "token_reduction_pct": 0.30,
    "clarification_reduction_pct": 0.25,
    "manual_correction_reduction_pct": 0.20,
    "validated_confidence_delta": 0.15,
    "safety_error_reduction_pct": 0.10,
}


VARIANT_LABELS = {
    "ai_kit": "AI Kit",
    "docs": "Docs baseline",
    "docs_mcp": "Docs baseline",
    "no_context": "No-context baseline",
}


@dataclass(frozen=True)
class Run:
    case_id: str
    case_label: str
    variant: str
    group: str
    tokens: int
    clarification_turns: int
    manual_corrections: int
    skill_checklist_pass_rate: float
    validated_confidence_rate: float
    safety_errors: int


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate for text/code when provider telemetry is absent."""
    chunks = re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text)
    return len(chunks)


def as_int(value: Any, default: int = 0) -> int:
    return default if value is None else int(value)


def as_float(value: Any, default: float = 0.0) -> float:
    return default if value is None else float(value)


def validated_confidence(item: dict[str, Any]) -> float:
    if "validated_confidence_rate" in item:
        return as_float(item["validated_confidence_rate"])

    checklist = as_float(
        item.get("skill_checklist_pass_rate", item.get("checklist_pass_rate"))
    )
    sme = as_float(item.get("sme_review_score"), 50.0)
    sandbox = as_float(item.get("sandbox_execution_score"), 0.0)
    return round(checklist * 0.70 + sme * 0.20 + sandbox * 0.10, 1)


def load_payload(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {"metadata": {}, "runs": raw}
    return {"metadata": raw.get("metadata", {}), "runs": raw.get("runs", [])}


def load_runs(path: Path) -> tuple[dict[str, Any], list[Run]]:
    payload = load_payload(path)
    runs: list[Run] = []

    for item in payload["runs"]:
        token_value = item.get("total_tokens_to_acceptance")
        if token_value is None:
            token_value = estimate_tokens(
                f"{item.get('prompt', '')}\n{item.get('response', '')}"
            )

        checklist = as_float(
            item.get("skill_checklist_pass_rate", item.get("checklist_pass_rate"))
        )

        variant = str(item["variant"])
        # Normalize old docs_mcp name while keeping backward compatibility.
        normalized_variant = "docs" if variant == "docs_mcp" else variant

        case_id = str(item["case_id"])
        group = item.get("group")
        if group is None:
            group = "production" if case_id.startswith("prod_") else "prompt_only"

        runs.append(
            Run(
                case_id=case_id,
                case_label=str(item.get("case_label", case_id)),
                variant=normalized_variant,
                group=str(group),
                tokens=as_int(token_value),
                clarification_turns=as_int(item.get("clarification_turns")),
                manual_corrections=as_int(item.get("manual_corrections")),
                skill_checklist_pass_rate=checklist,
                validated_confidence_rate=validated_confidence(item),
                safety_errors=as_int(item.get("safety_errors")),
            )
        )

    return payload["metadata"], runs


def pct_reduction(baseline: float, ai_kit: float) -> float:
    if baseline <= 0:
        return 0.0 if ai_kit <= 0 else -100.0
    return ((baseline - ai_kit) / baseline) * 100


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


def compare(ai: Run, baseline: Run) -> dict[str, Any]:
    token_reduction = pct_reduction(baseline.tokens, ai.tokens)
    clarification_reduction = pct_reduction(
        baseline.clarification_turns, ai.clarification_turns
    )
    correction_reduction = pct_reduction(
        baseline.manual_corrections, ai.manual_corrections
    )
    confidence_delta = (
        ai.validated_confidence_rate - baseline.validated_confidence_rate
    )
    safety_reduction = pct_reduction(baseline.safety_errors, ai.safety_errors)

    efficiency_gain = (
        WEIGHTS["token_reduction_pct"] * token_reduction
        + WEIGHTS["clarification_reduction_pct"] * clarification_reduction
        + WEIGHTS["manual_correction_reduction_pct"] * correction_reduction
        + WEIGHTS["validated_confidence_delta"] * confidence_delta
        + WEIGHTS["safety_error_reduction_pct"] * safety_reduction
    )

    return {
        "case_id": ai.case_id,
        "case_label": ai.case_label,
        "group": ai.group,
        "baseline": baseline.variant,
        "ai_tokens": ai.tokens,
        "baseline_tokens": baseline.tokens,
        "token_reduction_pct": token_reduction,
        "ai_clarifications": ai.clarification_turns,
        "baseline_clarifications": baseline.clarification_turns,
        "ai_corrections": ai.manual_corrections,
        "baseline_corrections": baseline.manual_corrections,
        "ai_skill_checklist": ai.skill_checklist_pass_rate,
        "baseline_skill_checklist": baseline.skill_checklist_pass_rate,
        "ai_validated_confidence": ai.validated_confidence_rate,
        "baseline_validated_confidence": baseline.validated_confidence_rate,
        "ai_safety_errors": ai.safety_errors,
        "baseline_safety_errors": baseline.safety_errors,
        "efficiency_gain": efficiency_gain,
        "decision": decision(efficiency_gain, ai.safety_errors),
    }


def group_by_case(runs: Iterable[Run]) -> dict[str, dict[str, Run]]:
    grouped: dict[str, dict[str, Run]] = {}
    for run in runs:
        grouped.setdefault(run.case_id, {})[run.variant] = run
    return grouped


def score_runs(runs: list[Run], baselines: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _case_id, variants in sorted(group_by_case(runs).items()):
        ai = variants.get("ai_kit")
        if not ai:
            continue
        for baseline_name in baselines:
            baseline = variants.get(baseline_name)
            if baseline:
                rows.append(compare(ai, baseline))
    return rows


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "avg_efficiency_gain_pct": 0,
            "ai_tokens": 0,
            "baseline_tokens": 0,
            "token_reduction_pct": 0,
        }
    ai_tokens = sum(row["ai_tokens"] for row in rows)
    baseline_tokens = sum(row["baseline_tokens"] for row in rows)
    return {
        "avg_efficiency_gain_pct": round(
            sum(row["efficiency_gain"] for row in rows) / len(rows), 1
        ),
        "ai_tokens": ai_tokens,
        "baseline_tokens": baseline_tokens,
        "token_reduction_pct": round(pct_reduction(baseline_tokens, ai_tokens), 1),
    }


def render_report(rows: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    title = metadata.get("title", "AI Kit Eval Score")
    lines = [
        f"# {title}",
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
        "| Case | Baseline | AI tokens | Baseline tokens | Token reduction | Skill rubric AI/Baseline | Validated confidence AI/Baseline | Safety AI/Baseline | Gain | Decision |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in rows:
        lines.append(
            "| {case_label} | {baseline} | {ai_tokens:,} | {baseline_tokens:,} | {token_reduction} | {ai_checklist:.1f}% / {baseline_checklist:.1f}% | {ai_confidence:.1f}% / {baseline_confidence:.1f}% | {ai_safety_errors} / {baseline_safety_errors} | {gain} | {decision} |".format(
                case_label=row["case_label"],
                baseline=VARIANT_LABELS.get(row["baseline"], row["baseline"]),
                ai_tokens=row["ai_tokens"],
                baseline_tokens=row["baseline_tokens"],
                token_reduction=format_pct(row["token_reduction_pct"]),
                ai_checklist=row["ai_skill_checklist"],
                baseline_checklist=row["baseline_skill_checklist"],
                ai_confidence=row["ai_validated_confidence"],
                baseline_confidence=row["baseline_validated_confidence"],
                ai_safety_errors=row["ai_safety_errors"],
                baseline_safety_errors=row["baseline_safety_errors"],
                gain=format_pct(row["efficiency_gain"]),
                decision=row["decision"],
            )
        )

    agg = aggregate(rows)
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Average efficiency gain: `{agg['avg_efficiency_gain_pct']:.1f}%`",
            f"- AI Kit tokens: `{agg['ai_tokens']:,}`",
            f"- Baseline tokens: `{agg['baseline_tokens']:,}`",
            f"- Token reduction: `{agg['token_reduction_pct']:.1f}%`",
            "",
            "## Notes",
            "",
            "- `Skill rubric` is checklist coverage, not final quality confidence.",
            "- `Validated confidence` includes SME and sandbox status when available.",
            "- Use real provider token telemetry when available; otherwise deterministic text estimates are acceptable for pilot comparisons.",
        ]
    )
    return "\n".join(lines) + "\n"


def rows_for_group(rows: list[dict[str, Any]], group: str, baseline: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["group"] == group and row["baseline"] == baseline]


def chart_data(metadata: dict[str, Any], runs: list[Run], rows: list[dict[str, Any]]) -> dict[str, Any]:
    prompt_rows = rows_for_group(rows, "prompt_only", "no_context")
    production_ai = [run for run in runs if run.group == "production" and run.variant == "ai_kit"]
    production_docs = [run for run in runs if run.group == "production" and run.variant == "docs"]
    production_no_context = [run for run in runs if run.group == "production" and run.variant == "no_context"]

    return {
        "title": metadata.get("title", "Xsolla AI Kit Metrics Dashboard"),
        "ready_skills": metadata.get("ready_skills", []),
        "excluded_skills": metadata.get("excluded_skills", []),
        "aggregate": aggregate(rows),
        "prompt_only": {
            "cases": [row["case_label"] for row in prompt_rows],
            "ai_kit_tokens": [row["ai_tokens"] for row in prompt_rows],
            "no_context_tokens": [row["baseline_tokens"] for row in prompt_rows],
            "ai_kit_skill_rubric_pct": [row["ai_skill_checklist"] for row in prompt_rows],
            "ai_kit_validated_confidence_pct": [row["ai_validated_confidence"] for row in prompt_rows],
            "no_context_validated_confidence_pct": [row["baseline_validated_confidence"] for row in prompt_rows],
            "ai_kit_efficiency_gain_pct": [round(row["efficiency_gain"], 1) for row in prompt_rows],
        },
        "production": {
            "cases": [run.case_label for run in production_ai],
            "ai_kit_tokens": [run.tokens for run in production_ai],
            "docs_tokens": [run.tokens for run in production_docs],
            "no_context_tokens": [run.tokens for run in production_no_context],
            "ai_kit_validated_confidence_pct": [run.validated_confidence_rate for run in production_ai],
            "docs_validated_confidence_pct": [run.validated_confidence_rate for run in production_docs],
            "no_context_validated_confidence_pct": [run.validated_confidence_rate for run in production_no_context],
            "clarifications": [
                sum(run.clarification_turns for run in production_ai),
                sum(run.clarification_turns for run in production_docs),
                sum(run.clarification_turns for run in production_no_context),
            ],
            "manual_corrections": [
                sum(run.manual_corrections for run in production_ai),
                sum(run.manual_corrections for run in production_docs),
                sum(run.manual_corrections for run in production_no_context),
            ],
            "safety_errors": [
                sum(run.safety_errors for run in production_ai),
                sum(run.safety_errors for run in production_docs),
                sum(run.safety_errors for run in production_no_context),
            ],
        },
    }


def js_array(values: list[Any]) -> str:
    return json.dumps(values, ensure_ascii=False)


def render_canvas(data: dict[str, Any]) -> str:
    prompt = data["prompt_only"]
    prod = data["production"]
    agg = data["aggregate"]
    ready_skills = data.get("ready_skills", [])
    excluded_skills = data.get("excluded_skills", [])

    prod_docs_tokens = prod.get("docs_tokens", [])
    docs_reduction = 0.0
    if prod_docs_tokens:
        ai_total = sum(prod["ai_kit_tokens"])
        docs_total = sum(prod_docs_tokens)
        docs_reduction = round(pct_reduction(docs_total, ai_total), 1)

    return f'''import {{
  BarChart,
  Card,
  CardBody,
  CardHeader,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
}} from "cursor/canvas";

const readySkills = {js_array(ready_skills)};
const excludedSkills = {js_array(excluded_skills)};
const promptCases = {js_array(prompt["cases"])};
const promptAiTokens = {js_array(prompt["ai_kit_tokens"])};
const promptBaselineTokens = {js_array(prompt["no_context_tokens"])};
const promptChecklistAi = {js_array(prompt["ai_kit_skill_rubric_pct"])};
const promptConfidenceAi = {js_array(prompt["ai_kit_validated_confidence_pct"])};
const promptConfidenceBaseline = {js_array(prompt["no_context_validated_confidence_pct"])};
const promptEfficiencyGain = {js_array(prompt["ai_kit_efficiency_gain_pct"])};
const productionCases = {js_array(prod["cases"])};
const prodAiTokens = {js_array(prod["ai_kit_tokens"])};
const prodDocsTokens = {js_array(prod.get("docs_tokens", []))};
const prodNoContextTokens = {js_array(prod.get("no_context_tokens", []))};
const prodRiskAi = {js_array(prod["ai_kit_validated_confidence_pct"])};
const prodRiskDocs = {js_array(prod.get("docs_validated_confidence_pct", []))};
const prodRiskNoContext = {js_array(prod.get("no_context_validated_confidence_pct", []))};
const prodClarifications = {js_array(prod["clarifications"])};
const prodCorrections = {js_array(prod["manual_corrections"])};
const prodSafety = {js_array(prod["safety_errors"])};

function DecisionDiagram() {{
  const theme = useHostTheme();
  const box = {{
    border: `1px solid ${{theme.stroke.secondary}}`,
    background: theme.fill.tertiary,
    borderRadius: 8,
    padding: 12,
  }};
  const arrow = {{ color: theme.text.tertiary, fontSize: 18, alignSelf: "center" }};
  return (
    <Grid columns="1fr 28px 1fr 28px 1fr 28px 1fr" gap={{8}} align="stretch">
      <Stack gap={{6}} style={{box}}>
        <Text weight="semibold">Production task</Text>
        <Text size="small" tone="secondary">Partner asks for integration or issue fix.</Text>
      </Stack>
      <Text style={{arrow}}>→</Text>
      <Stack gap={{6}} style={{box}}>
        <Text weight="semibold">Choose variant</Text>
        <Text size="small" tone="secondary">AI Kit vs docs baseline vs no context.</Text>
      </Stack>
      <Text style={{arrow}}>→</Text>
      <Stack gap={{6}} style={{box}}>
        <Text weight="semibold">Measure</Text>
        <Text size="small" tone="secondary">Tokens, corrections, safety, confidence.</Text>
      </Stack>
      <Text style={{arrow}}>→</Text>
      <Stack gap={{6}} style={{box}}>
        <Text weight="semibold">Decision</Text>
        <Text size="small" tone="secondary">Use when validated confidence improves and safety errors are zero.</Text>
      </Stack>
    </Grid>
  );
}}

export default function AiKitEvalDashboard() {{
  return (
    <Stack gap={{18}} style={{{{ padding: 20 }}}}>
      <Stack gap={{6}}>
        <H1>{data["title"]}</H1>
        <Text tone="secondary">
          Reusable AI Kit eval dashboard. Token counts can use provider telemetry or deterministic text estimates.
          Skill-rubric coverage is separated from validated confidence.
        </Text>
      </Stack>

      <Grid columns={{4}} gap={{12}}>
        <Stat value="{agg["avg_efficiency_gain_pct"]:.1f}%" label="Avg AI Kit efficiency gain" tone="success" />
        <Stat value="{agg["token_reduction_pct"]:.1f}%" label="All-run token reduction" tone="success" />
        <Stat value="{{prodRiskAi.length ? Math.round(prodRiskAi.reduce((a, b) => a + b, 0) / prodRiskAi.length) : 0}}%" label="Validated AI Kit confidence" tone="success" />
        <Stat value="{docs_reduction:.1f}%" label="Token reduction vs docs" tone="info" />
      </Grid>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>Metric 1: Tokens To Accepted Result</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">Y-axis: tokens. X-axis: eval case. Lower is better.</Text>
            <BarChart
              categories={{promptCases}}
              series={{[
                {{ name: "AI Kit", data: promptAiTokens, tone: "success" }},
                {{ name: "No-context baseline", data: promptBaselineTokens, tone: "warning" }},
              ]}}
              height={{260}}
              valueSuffix=" tokens"
              showValues
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Metric 2: Skill Rubric vs Validated Confidence</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">Y-axis: percent. X-axis: eval case. 100% rubric is not 100% production confidence.</Text>
            <BarChart
              categories={{promptCases}}
              series={{[
                {{ name: "AI Kit skill rubric", data: promptChecklistAi, tone: "success" }},
                {{ name: "AI Kit validated confidence", data: promptConfidenceAi, tone: "info" }},
                {{ name: "No-context validated confidence", data: promptConfidenceBaseline, tone: "warning" }},
              ]}}
              height={{260}}
              yMax={{100}}
              valueSuffix="%"
              showValues
            />
          </CardBody>
        </Card>
      </Grid>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>Metric 3: Production-Risk Validated Confidence</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">Y-axis: validated confidence. X-axis: production-informed case.</Text>
            <BarChart
              categories={{productionCases}}
              series={{[
                {{ name: "AI Kit", data: prodRiskAi, tone: "success" }},
                {{ name: "Docs baseline", data: prodRiskDocs, tone: "info" }},
                {{ name: "No-context baseline", data: prodRiskNoContext, tone: "warning" }},
              ]}}
              height={{260}}
              yMax={{100}}
              valueSuffix="%"
              showValues
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Metric 4: Clarifications And Corrections</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">Y-axis: count. X-axis: variant. Lower is better.</Text>
            <BarChart
              categories={{["AI Kit", "Docs", "No context"]}}
              series={{[
                {{ name: "Clarifications", data: prodClarifications, tone: "info" }},
                {{ name: "Manual corrections", data: prodCorrections, tone: "warning" }},
              ]}}
              height={{260}}
              showValues
            />
          </CardBody>
        </Card>
      </Grid>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>Metric 5: Safety Errors</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">Y-axis: critical safety errors. X-axis: variant. Target is zero.</Text>
            <BarChart
              categories={{["AI Kit", "Docs", "No context"]}}
              series={{[{{ name: "Safety errors", data: prodSafety, tone: "danger" }}]}}
              height={{230}}
              showValues
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Metric 6: AI Kit Efficiency Gain</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">Y-axis: weighted gain. X-axis: eval case. Strong value threshold is 25%.</Text>
            <BarChart
              categories={{promptCases}}
              series={{[{{ name: "Efficiency gain", data: promptEfficiencyGain, tone: "success" }}]}}
              referenceLines={{[{{ value: 25, label: "Strong value", tone: "success" }}]}}
              height={{230}}
              yMax={{80}}
              valueSuffix="%"
              showValues
            />
          </CardBody>
        </Card>
      </Grid>

      <Stack gap={{8}}>
        <H2>Decision Diagram</H2>
        <DecisionDiagram />
      </Stack>

      <Card>
        <CardHeader>Final Decision</CardHeader>
        <CardBody>
          <Stack gap={{8}}>
            <H3>Use AI Kit for ready skills; keep docs as the fair baseline.</H3>
            <Text>AI Kit value is fewer missed failure modes and fewer correction loops, not only token savings.</Text>
            <Row gap={{8}} wrap>
              {{readySkills.map((skill) => <Pill active>{{skill}}</Pill>)}}
            </Row>
            <Text tone="secondary">Excluded until real content exists: {{excludedSkills.join(", ")}}.</Text>
          </Stack>
        </CardBody>
      </Card>
    </Stack>
  );
}}
'''


def write_outputs(
    out_dir: Path,
    metadata: dict[str, Any],
    runs: list[Run],
    rows: list[dict[str, Any]],
    report_name: str,
    score_name: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    visual_dir = out_dir / "visualizations"
    visual_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / report_name).write_text(render_report(rows, metadata), encoding="utf-8")
    (out_dir / score_name).write_text(json.dumps(rows, indent=2), encoding="utf-8")

    data = chart_data(metadata, runs, rows)
    (visual_dir / "ai-kit-dashboard-data.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    (visual_dir / "ai-kit-eval-dashboard.canvas.tsx").write_text(
        render_canvas(data), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AI Kit skill runs.")
    parser.add_argument("input", type=Path, help="Path to eval runs JSON.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("testing/eval-output"),
        help="Output directory for report, score JSON, dashboard data, and canvas.",
    )
    parser.add_argument(
        "--baselines",
        default="docs,no_context",
        help="Comma-separated baseline variants to compare against.",
    )
    parser.add_argument("--report-name", default="ai-kit-eval-report.md")
    parser.add_argument("--score-name", default="ai-kit-eval-score.json")
    args = parser.parse_args()

    metadata, runs = load_runs(args.input)
    baselines = [item.strip() for item in args.baselines.split(",") if item.strip()]
    rows = score_runs(runs, baselines)
    write_outputs(args.out_dir, metadata, runs, rows, args.report_name, args.score_name)

    print(render_report(rows, metadata))
    print(f"Wrote outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
