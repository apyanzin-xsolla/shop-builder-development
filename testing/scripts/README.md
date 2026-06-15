# AI Kit Eval Scripts

## `ai_kit_eval.py`

Single reusable script for future AI Kit skills.

It scores eval runs and generates:

- Markdown report
- scored JSON
- dashboard data JSON
- Cursor Canvas dashboard source with the same visualization style

Run:

```bash
python3 testing/scripts/ai_kit_eval.py testing/ai-kit-real-eval-runs.json --out-dir testing/generated-eval
```

Expected output:

```text
testing/generated-eval/ai-kit-eval-report.md
testing/generated-eval/ai-kit-eval-score.json
testing/generated-eval/visualizations/ai-kit-dashboard-data.json
testing/generated-eval/visualizations/ai-kit-eval-dashboard.canvas.tsx
```

This is the script to copy into `xsolla-ai-kit` for the next skills.

## `score_ai_kit_eval.py`

Scores AI Kit eval runs from JSON.

Run against no-context baseline:

```bash
python3 testing/scripts/score_ai_kit_eval.py testing/ai-kit-eval-runs.sample.json --baseline no_context
```

Run against docs baseline:

```bash
python3 testing/scripts/score_ai_kit_eval.py testing/ai-kit-eval-runs.sample.json --baseline docs_mcp
```

Run both baselines and export machine-readable output:

```bash
python3 testing/scripts/score_ai_kit_eval.py testing/ai-kit-eval-runs.sample.json --baseline all --json-output testing/ai-kit-eval-score.json
```

## Input Schema

```json
{
  "runs": [
    {
      "case_id": "catalog_design",
      "variant": "ai_kit",
      "total_tokens_to_acceptance": 720,
      "clarification_turns": 0,
      "manual_corrections": 0,
      "checklist_pass_rate": 100,
      "safety_errors": 0
    }
  ]
}
```

If `total_tokens_to_acceptance` is missing, the script estimates tokens from `prompt + response` using:

```text
tokens ~= characters / 4
```

Use real provider token telemetry when available.

## Output

The script prints a Markdown table with:

- AI Kit tokens.
- Baseline tokens.
- Token reduction.
- Skill-rubric checklist delta.
- Validated confidence delta.
- Safety errors.
- AI Kit Efficiency Gain.
- Decision.

