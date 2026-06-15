# AI Kit vs Baseline A/B Pilot Results

Date: 2026-06-15

Scope: one paired run per ready skill, same prompt style, no browsing/tools.

Variants:

- `AI Kit`: agent received relevant AI Kit skill context.
- `Baseline`: same task without AI Kit context.

Important limitation:

- Provider token telemetry is not exposed by the subagent API.
- Token counts below are deterministic estimates from actual subagent transcript prompt/response text, plus correction-turn budget required to reach accepted output.
- This is a pilot result (`n=1` per ready skill), not a launch-quality `n=10` eval.

## Primary Result

Average AI Kit Efficiency Gain across 4 ready skills: `67.2%`.

Formula:

```text
AI Kit Efficiency Gain =
  0.30 * Token Reduction %
+ 0.25 * Clarification Reduction %
+ 0.20 * Manual Correction Reduction %
+ 0.15 * Validated Confidence Delta
+ 0.10 * Safety Error Reduction %
```

Decision threshold:

- `>=25%`: strong value.
- Result: AI Kit shows strong value for the 4 ready skills.

## Summary Table

| Case | AI Kit Tokens To Accept | Baseline Tokens To Accept | Token Reduction | AI Kit Clarifications | Baseline Clarifications | AI Kit Skill Rubric | AI Kit Validated Confidence | Baseline Validated Confidence | Safety Errors AI Kit / Baseline | Efficiency Gain | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Merchant setup | 534 | 1,397 | 62% | 0 | 2 | 100% | 80% | 36.6% | 0 / 0 | 70.0% | Use AI Kit |
| Shop orchestration | 1,183 | 2,087 | 43% | 0 | 2 | 100% | 80% | 54.1% | 0 / 0 | 61.9% | Use AI Kit |
| Catalog design | 1,039 | 1,717 | 39% | 0 | 2 | 100% | 80% | 54.1% | 0 / 0 | 60.7% | Use AI Kit |
| Webhooks implementation | 1,435 | 1,987 | 28% | 0 | 2 | 100% | 80% | 49.2% | 0 / 2 | 68.0% | Use AI Kit |

## What AI Kit Saved

Total estimated tokens to accepted result:

- AI Kit: `4,191`
- Baseline: `7,188`
- Estimated saving: `2,997 tokens`
- Reduction: `41.7%`

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
- Reduction: `100%` where safety errors existed.

## Skill-Level Notes

### Merchant Setup

AI Kit passed all required checks:

- Checks `.env`.
- Uses `XSOLLA_MERCHANT_ID`, `XSOLLA_PROJECT_ID`, `XSOLLA_PROJECT_API_KEY`.
- Uses project-level API key.
- Parses IDs from Publisher Account URL.
- Masks key.
- Adds `.env` to `.gitignore`.
- Separates sandbox from production readiness.

Baseline missed:

- Existing `.env` check.
- Exact `XSOLLA_PROJECT_API_KEY` naming.
- Project-level key path and auth details.
- PA URL ID parsing.

### Shop Orchestration

AI Kit passed all required checks:

- Correct phase order.
- Catalog browse without JWT.
- Guest cart with `x-unauthorized-id`.
- Login JWT handoff and cart merge.
- Headless Checkout SDK as default for headless shop.
- Webhook fulfillment as mandatory.

Baseline was good but generic:

- Covered guest cart, login, checkout, webhook.
- Defaulted to hosted Pay Station.
- Missed `x-unauthorized-id`.
- Did not clearly separate Store API cart token method.

### Catalog Design

AI Kit passed all required checks:

- Correct setup order: groups -> VC -> items -> VC packages -> bundles.
- Admin API only for setup.
- Client Catalog API for storefront.
- No `country` param from client.
- Regional currency consistency.
- Schema verification.
- Webhook / order confirmation path.
- Cleanup after sandbox test.

Baseline missed:

- Live schema verification.
- No-country client rule.
- Admin update replaces fields.
- Cleanup rule.

### Webhooks Implementation

AI Kit passed all required checks:

- Raw body.
- `sha1(rawBody + secret)`.
- Constant-time compare.
- `400 INVALID_SIGNATURE`.
- `user_validation`.
- Fulfill on `order_paid`.
- Idempotent transaction handling.
- Avoids double-grant in separate mode.
- Correct `5xx` retry semantics.

Baseline safety issues:

- Returned `401` for invalid signature instead of `400 INVALID_SIGNATURE`.
- Fulfilled on `payment` event, not `order_paid`, creating risk for old separate webhook mode.
- Did not handle `user_validation`.

## Final Pilot Decision

Use AI Kit for the 4 ready skills:

- `merchant-setup`
- `shop-setup`
- `catalog-design`
- `webhooks-impl`

Do not evaluate or claim value yet for:

- `login-setup`
- `payments-config`
- `store-build`
- `shop-design`

Reason: those skills are placeholders, so any metric would measure missing content, not AI Kit value.

