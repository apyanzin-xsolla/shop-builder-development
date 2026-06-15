# Xsolla AI Kit Eval Results

Date: 2026-06-15

Current result: pilot A/B eval complete for 4 ready skills, plus production-informed eval on 2 real-risk cases.

Full details:

- `ai-kit-ab-pilot-results.md`
- `ai-kit-production-informed-results.md`

## Result

### Prompt-Only Pilot

Average AI Kit Efficiency Gain: `67.7%`.

Total estimated tokens to accepted result:

- AI Kit: `3,230`
- Baseline without AI Kit: `5,920`
- Saved: `2,690 tokens`
- Token reduction: `45.4%`

Clarification turns:

- AI Kit: `0`
- Baseline: `8`
- Reduction: `100%`

Manual corrections:

- AI Kit: `0`
- Baseline: `14`
- Reduction: `100%`

Safety errors:

- AI Kit: `0`
- Baseline: `2`

### Production-Informed Pilot

Compared variants:

- `AI Kit`
- `Docs/MCP baseline`
- `No-context baseline`

Cases:

- Catalog regional pricing returns wrong/default currency.
- `order_paid` webhook returns intermittent HTTP 500.

Aggregate result:

| Variant | Tokens To Accept | Avg Checklist Pass | Clarifications | Corrections | Safety Errors | Production-Risk Coverage |
|---|---:|---:|---:|---:|---:|---:|
| AI Kit | 1,035 | 100% | 0 | 0 | 0 | 100% |
| Docs/MCP baseline | 1,180 | 82.5% | 2 | 2 | 0 | 82.5% |
| No-context baseline | 2,250 | 62.5% | 4 | 6 | 1 | 62.5% |

AI Kit impact:

- vs no-context: `54.0%` estimated token reduction, `+37.5 pp` production-risk coverage.
- vs Docs/MCP baseline: `12.3%` estimated token reduction, `+17.5 pp` production-risk coverage.

## Decision

Use AI Kit for ready skills:

- `merchant-setup`
- `shop-setup`
- `catalog-design`
- `webhooks-impl`

Do not evaluate or claim value yet for placeholder skills:

- `login-setup`
- `payments-config`
- `store-build`
- `shop-design`

## Metric Formula

```text
AI Kit Efficiency Gain =
  0.30 * Token Reduction %
+ 0.25 * Clarification Reduction %
+ 0.20 * Manual Correction Reduction %
+ 0.15 * Checklist Pass Rate Delta
+ 0.10 * Safety Error Reduction %
```

## Limitation

This is a pilot result:

- Prompt-only pilot: `n=1` paired run per ready skill.
- Production-informed pilot: `n=2` real-risk cases, 3 variants.
- Token counts are estimated because provider token telemetry is not exposed by the subagent API.
- No live sandbox API calls were executed.

For launch confidence, rerun with:

```text
4 ready skills * 3 variants * 10 runs = 120 runs
```

