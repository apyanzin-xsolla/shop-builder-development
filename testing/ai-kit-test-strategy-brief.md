# AI Kit Test Strategy Brief

Date: 2026-06-15

## Goal

Test whether `xsolla-ai-kit` improves real Xsolla integration work compared with agents that do not use the skills.

We are not testing the repository quality. We are testing product value: does AI Kit reduce tokens, clarifications, mistakes, and production-risk gaps?

## Variants

Each case should be tested in 3 variants:

- `AI Kit`: agent uses AI Kit skill context.
- `Docs/MCP baseline`: agent uses current Xsolla docs / MCP, but no AI Kit skill.
- `No-context baseline`: agent answers without AI Kit or special Xsolla context.

## Skills In Scope

Ready to evaluate:

- `merchant-setup`
- `shop-setup`
- `catalog-design`
- `webhooks-impl`

Excluded until real skill content exists:

- `login-setup`
- `payments-config`
- `store-build`
- `shop-design`

## Metrics

Primary metric:

```text
AI Kit Efficiency Gain =
  0.30 * Token Reduction %
+ 0.25 * Clarification Reduction %
+ 0.20 * Manual Correction Reduction %
+ 0.15 * Validated Confidence Delta
+ 0.10 * Safety Error Reduction %
```

Measured per run:

- Tokens to accepted result.
- Clarification turns.
- Manual corrections.
- Skill-rubric checklist pass rate.
- Validated confidence rate.
- Safety errors.
- Production-risk coverage.

## Production-Informed Cases

Use real support-like scenarios where possible:

- Catalog regional pricing returns wrong/default currency.
- `order_paid` webhook returns HTTP 500.
- Webhook retries risk duplicate grants.
- SKU mapping from Xsolla order to in-game item is unclear.
- Sandbox/project API key setup is confusing.

Production tests must be non-destructive:

- No production API keys.
- No real merchant writes.
- No real player data.
- No real payment attempts.

## Decision Rule

Use AI Kit for a skill if:

- Token reduction is at least `20%`, or quality improves while token cost stays neutral.
- Clarifications reduce by at least `50%`.
- Manual corrections reduce by at least `50%`.
- Validated confidence rate is at least `85%`.
- Safety errors are `0`.
- Production-risk validated confidence improves vs Docs/MCP baseline.

## Current Pilot Result

AI Kit wins for ready skills.

Prompt-only pilot:

- `67.7%` average AI Kit Efficiency Gain.
- `45.4%` estimated token reduction vs no-context baseline.
- `0` AI Kit safety errors.

Production-informed pilot:

- AI Kit: `80%` validated production-risk confidence in the current pilot.
- Docs/MCP baseline: `82.5%`.
- No-context baseline: `62.5%`.

Final recommendation: use AI Kit for ready skills, keep Docs/MCP as the fair baseline, and do not claim full end-to-end shop automation until unfinished skills are implemented.

