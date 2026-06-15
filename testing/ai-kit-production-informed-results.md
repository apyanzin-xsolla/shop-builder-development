# AI Kit Production-Informed Eval Results

Date: 2026-06-15

Purpose: add production-risk signals to the AI Kit evaluation.

This is not a repo QA pass. It tests whether AI Kit helps agents handle real Xsolla integration failure modes better than:

- No-context baseline.
- Docs/MCP-style baseline.

## Production Signals Used

Read-only Slack search found production-like signals:

- `order_paid` webhook endpoints returning HTTP 500 for real order IDs.
- Partner questions about mapping Xsolla SKUs from `order_paid` to in-game items/currencies.
- Dev/prod mismatch around combined vs separate webhook modes.
- Catalog local pricing returning an unexpected currency for a country-specific request.
- Project/sandbox API key setup confusion.

Datadog production logs were not available through MCP in this workspace, so this is a Slack/docs/skill-evidence pilot, not an observability-backed incident analysis.

## Variants

- `AI Kit`: agent gets relevant AI Kit skill context.
- `Docs/MCP baseline`: agent gets concise production/docs facts but no AI Kit workflow skill.
- `No-context baseline`: agent answers from general knowledge.

## Cases

### Case 1: Catalog Regional Pricing

Production case:

```text
Catalog API /items/bundle?locale=br&country=MX returns BRL instead of MXN.
Partner says MXN prices are configured for all bundles in Publisher Account.
```

Required production-risk checks:

- Question suspicious `locale=br` vs `country=MX`.
- Test without explicit `country` and from MX IP.
- Check bundle-level and child-item MXN prices.
- Check regional pricing completeness.
- Check currency/default-currency consistency.
- Avoid Admin API partial updates before GET-first.
- Verify live schema/docs before writes.
- Validate with controlled read-only request matrix.

Result:

| Variant | Tokens To Accept | Clarifications | Corrections | Checklist Pass | Safety Errors | Production-Risk Coverage |
|---|---:|---:|---:|---:|---:|---:|
| AI Kit | 1,069 | 0 | 0 | 100% | 0 | 100% |
| Docs/MCP baseline | 1,169 | 1 | 1 | 80% | 0 | 80% |
| No-context baseline | 1,430 | 2 | 3 | 55% | 0 | 55% |

AI Kit advantage:

- Adds Xsolla-specific rules: no-country client behavior, currency consistency, GET-before-update, schema verification.
- Baseline focuses mostly on `locale=br`, which is useful but incomplete.

### Case 2: `order_paid` Webhook 500s

Production case:

```text
A project occasionally responds to order_paid webhooks with HTTP 500.
Need partner checklist and safe production fix plan, including duplicate-grant prevention during retries.
```

Required production-risk checks:

- Ask for logs by known order IDs.
- Check whether fulfillment happened before HTTP 500.
- Verify raw-body signature validation.
- Handle combined vs separate webhook mode.
- Fulfill on `order_paid` / `order_canceled`, not both `payment` and `order_paid`.
- Use durable idempotency ledger / unique constraints.
- Return prior 2xx for duplicate already-processed events.
- Use 5xx only for transient failures.
- Keep handler fast and async heavy work.
- Reconcile known impacted paid orders safely.

Result:

| Variant | Tokens To Accept | Clarifications | Corrections | Checklist Pass | Safety Errors | Production-Risk Coverage |
|---|---:|---:|---:|---:|---:|---:|
| AI Kit | 742 | 0 | 0 | 100% | 0 | 100% |
| Docs/MCP baseline | 809 | 1 | 1 | 85% | 0 | 85% |
| No-context baseline | 1,355 | 2 | 3 | 70% | 1 | 70% |

AI Kit advantage:

- Stronger on raw-body signature, exact response semantics, combined/separate modes, and duplicate-grant prevention.
- Docs/MCP baseline is good but less explicit on Xsolla-specific failure modes.
- No-context baseline is useful but leaves too much to partner interpretation.

## Aggregate Result

| Variant | Total Tokens To Accept | Avg Checklist Pass | Clarifications | Corrections | Safety Errors | Avg Production-Risk Coverage |
|---|---:|---:|---:|---:|---:|---:|
| AI Kit | 1,811 | 100% | 0 | 0 | 0 | 100% |
| Docs/MCP baseline | 1,978 | 82.5% | 2 | 2 | 0 | 82.5% |
| No-context baseline | 2,785 | 62.5% | 4 | 6 | 1 | 62.5% |

Token impact:

- AI Kit vs no-context: saves `974` estimated tokens, `35.0%` reduction.
- AI Kit vs Docs/MCP baseline: saves `167` estimated tokens, `8.4%` reduction.

Quality impact:

- AI Kit vs no-context: `+37.5 pp` checklist pass rate.
- AI Kit vs Docs/MCP baseline: `+17.5 pp` checklist pass rate.

Production-risk impact:

- AI Kit covered `100%` of tested risk checks.
- Docs/MCP baseline covered `82.5%`.
- No-context baseline covered `62.5%`.

## Decision

Use AI Kit for production-risk workflows when the skill exists.

Reason:

- Compared with no-context baseline, AI Kit gives large gains in tokens, corrections, and risk coverage.
- Compared with Docs/MCP baseline, AI Kit gives smaller token gain but meaningful quality/risk gain.
- The main product value is not only token saving. It is fewer production-risk misses.

Best production evaluation design going forward:

```text
AI Kit vs Docs/MCP baseline vs No-context baseline
```

Use production cases from:

- Slack support threads.
- Anonymized partner incidents.
- Datadog/log failure categories when access is available.
- Sandbox clones of real merchant flows.

