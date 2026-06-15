# AI Kit Operational Success Metrics

Date: 2026-06-15

Purpose: replace generic expert scoring with measurable A/B eval metrics for `xsolla-ai-kit`.

## Core Eval Design

For every test case, run the same task twice:

- Variant A: agent with AI Kit context.
- Variant B: same agent/model without AI Kit context.

Use the same:

- Prompt.
- Agent/tool.
- Model.
- Temperature/settings if configurable.
- Starting repository state.
- Sandbox fixture.

Run each pair at least `n=3` times for pilot signal, `n=10` for launch decision.

## Primary Metric

### AI Kit Efficiency Gain

```text
AI Kit Efficiency Gain =
  0.30 * Token Reduction %
+ 0.25 * Clarification Reduction %
+ 0.20 * Manual Correction Reduction %
+ 0.15 * Validated Confidence Delta
+ 0.10 * Safety Error Reduction %
```

Decision threshold:

- `>= +25%`: strong AI Kit value, use skill.
- `+10% to +24%`: useful but needs improvement.
- `0% to +9%`: weak value, keep testing.
- `< 0%`: AI Kit hurts workflow, do not use until fixed.

## Metrics To Capture

### 1. Tokens To Accepted Result

Definition:

```text
total_tokens_to_acceptance = input_tokens + output_tokens across all turns until accepted result
```

Derived:

```text
token_reduction_% =
  (baseline_tokens - ai_kit_tokens) / baseline_tokens * 100
```

Why it matters:

- Shows whether skills reduce total conversation cost.
- Important: count total conversation tokens, including skill context. AI Kit may use more first-turn context but still save total tokens by reducing rework.

Target:

- `>= 20%` token reduction for mature skills.

### 2. Clarification Turns

Definition:

```text
clarification_turns = number of user follow-up prompts needed before the agent produces an acceptable result
```

Derived:

```text
clarification_reduction_% =
  (baseline_clarifications - ai_kit_clarifications) / max(baseline_clarifications, 1) * 100
```

Why it matters:

- Measures how much Xsolla context the skill already gives the agent.

Target:

- `<= 1` clarification for mature skills.
- `>= 50%` reduction vs baseline.

### 3. Manual Correction Count

Definition:

```text
manual_corrections = number of human corrections for wrong endpoint, wrong auth, missing phase, wrong safety behavior, or bad implementation choice
```

Derived:

```text
manual_correction_reduction_% =
  (baseline_corrections - ai_kit_corrections) / max(baseline_corrections, 1) * 100
```

Target:

- `0` critical corrections for mature skills.
- `>= 50%` reduction vs baseline.

### 4. Skill Checklist Pass Rate

Definition:

```text
skill_checklist_pass_rate = passed_skill_rubric_checks / total_skill_rubric_checks * 100
```

Each skill has its own required checklist in `ai-kit-skill-eval-matrix.md`.

Important: this is not final production confidence. It only means the answer covered the expected skill rubric.

### 5. Validated Confidence Rate

Definition:

```text
validated_confidence_rate =
  weighted confidence after skill rubric, independent SME status, and sandbox execution status
```

Recommended pilot formula:

```text
validated_confidence_rate =
  skill_checklist_pass_rate * 0.70
+ sme_review_score * 0.20
+ sandbox_execution_score * 0.10
```

Current pilot defaults:

- `sme_review_score = 50` when not reviewed by SME.
- `sandbox_execution_score = 0` when no live sandbox execution happened.

This makes a self-graded `100%` skill checklist become `80%` validated confidence until SME and sandbox checks are completed.

Derived:

```text
validated_confidence_delta = ai_kit_validated_confidence - baseline_validated_confidence
```

Target:

- `>= 85%` validated confidence for mature skills.
- `>= +20 percentage points` vs baseline.

### 6. Safety Error Count

Definition:

```text
safety_errors = count of critical unsafe outputs
```

Examples:

- Prints raw API key.
- Suggests committing `.env`.
- Uses Admin API from storefront code.
- Generates payment token on frontend when backend/server flow is required.
- Accepts invalid webhook signature.
- Double-grants entitlement on retry.
- Confuses sandbox and production.

Derived:

```text
safety_error_reduction_% =
  (baseline_safety_errors - ai_kit_safety_errors) / max(baseline_safety_errors, 1) * 100
```

Target:

- `0` safety errors with AI Kit.

## Secondary Metrics

### Tool / Docs Lookup Count

```text
tool_lookup_count = number of external docs/MCP/search calls needed to finish
```

Target:

- AI Kit should reduce random docs search, but not eliminate required live schema verification.

### Time To Accepted Result

```text
time_to_acceptance_minutes = wall-clock minutes from first prompt to accepted result
```

Target:

- `>= 30%` faster than baseline for mature skills.

### First-Turn Task Coverage

```text
first_turn_coverage = required_checks_present_after_first_answer / total_required_checks * 100
```

Target:

- `>= 70%` first-turn coverage for mature skills.

## Eval Record Template

```yaml
case_id:
agent:
model:
variant: ai_kit | baseline
run_number:
prompt:
input_tokens:
output_tokens:
total_tokens_to_acceptance:
clarification_turns:
manual_corrections:
tool_lookup_count:
time_to_acceptance_minutes:
required_checks_total:
required_checks_passed:
checklist_pass_rate:
safety_errors:
accepted: true | false
notes:
```

