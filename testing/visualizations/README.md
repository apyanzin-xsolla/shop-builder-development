# AI Kit Visualizations

This folder stores the AI Kit dashboard source and the data used to generate all charts.

## Files

- `ai-kit-eval-dashboard.canvas.tsx` — Cursor Canvas dashboard source.
- `ai-kit-dashboard-data.json` — raw chart data and decision table values.

## Visualizations Included

The dashboard contains:

- KPI strip: AI Kit efficiency gain, token reduction, production-risk coverage.
- Metric definitions table.
- Tokens to accepted result chart.
- Skill rubric vs validated confidence chart.
- Production-risk validated confidence chart.
- Clarifications and manual corrections chart.
- Safety errors chart.
- AI Kit efficiency gain chart.
- Production-informed decision table.
- Decision flow diagram.
- Final decision block.

## Final Decision

Use AI Kit for ready skills:

- `merchant-setup`
- `shop-setup`
- `catalog-design`
- `webhooks-impl`

Keep Docs/MCP as the fair baseline for future comparisons.

Do not include unfinished skills in the decision until real skill content exists:

- `login-setup`
- `payments-config`
- `store-build`
- `shop-design`

