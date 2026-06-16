# AI Kit Eval Report

| Case | Baseline | AI tokens | Baseline tokens | Token reduction | Validated confidence AI/Baseline | Safety AI/Baseline | Gain | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---|
| merchant_setup | no_context | 534 | 1,397 | 61.8% | 80.0% / 36.6% | 0 / 0 | 70.0% | Use AI Kit |
| shop_orchestration | no_context | 1,183 | 2,087 | 43.3% | 80.0% / 54.1% | 0 / 0 | 61.9% | Use AI Kit |
| catalog_design | no_context | 1,039 | 1,717 | 39.5% | 80.0% / 54.1% | 0 / 0 | 60.7% | Use AI Kit |
| webhooks_impl | no_context | 1,435 | 1,987 | 27.8% | 80.0% / 49.2% | 0 / 2 | 68.0% | Use AI Kit |
| prod_catalog_pricing | docs | 1,069 | 1,169 | 8.6% | 80.0% / 66.0% | 0 / 0 | 49.7% | Use AI Kit |
| prod_catalog_pricing | no_context | 1,069 | 1,430 | 25.2% | 80.0% / 48.5% | 0 / 0 | 57.3% | Use AI Kit |
| prod_webhook_500s | docs | 742 | 809 | 8.3% | 80.0% / 69.5% | 0 / 0 | 49.1% | Use AI Kit |
| prod_webhook_500s | no_context | 742 | 1,355 | 45.2% | 80.0% / 59.0% | 0 / 1 | 71.7% | Use AI Kit |

## Aggregate

- Average efficiency gain: `61.1%`
- Token reduction: `34.6%`

Notes:
- `Validated confidence` is not raw checklist coverage.
- Use provider token telemetry when available; otherwise deterministic estimates are OK for pilot runs.
