# AI Kit Skill Eval Matrix

Date: 2026-06-15

Use this matrix to test AI Kit vs no-AI-Kit baseline. It is designed for production-like evaluation, not repository QA.

## How To Run

For each case:

1. Run the prompt with AI Kit context.
2. Run the same prompt without AI Kit context.
3. Use same agent, model, repo state, and sandbox fixture.
4. Capture metrics from `ai-kit-operational-metrics.md`.
5. Compare deltas.

Minimum pilot sample:

```text
4 skills * 2 variants * 3 runs = 24 runs
```

Launch-quality sample:

```text
4 skills * 2 variants * 10 runs = 80 runs
```

## Matrix

| Case | Skill | Test Prompt | Required Checks | Success Targets | Failure Conditions |
|---|---|---|---|---|---|
| Merchant setup | `merchant-setup` | "I need to start a sandbox Xsolla integration for a headless game shop. Help me find merchant ID, project ID, generate the right API key, and store credentials safely for local development." | Checks existing `.env`; explains PA signup; parses merchant/project ID from URL; chooses project-level API key; masks key; writes `XSOLLA_*`; protects `.env` in `.gitignore`; explains sandbox vs production. | `>=20%` token reduction; `<=1` clarification; `0` safety errors; `>=85%` validated confidence after SME/sandbox status. | Prints raw key; suggests committing `.env`; uses wrong key scope; skips sandbox/prod distinction. |
| Shop orchestration | `shop-setup` | "Build a full Xsolla headless shop plan for a mobile F2P game. It needs catalog browsing, guest cart, Login, checkout, webhook fulfillment, and production readiness." | Correct phase order; separates frontend/backend/Xsolla roles; includes guest cart; includes Login/JWT handoff; chooses Headless Checkout SDK default; includes webhook fulfillment; identifies production-readiness gaps. | `>=20%` token reduction; `>=50%` clarification reduction; `>=85%` validated confidence; `0` critical wrong-order decisions. | Starts with payment only; skips webhook; treats Login as required for browsing; confuses Pay Station redirect with default embedded checkout. |
| Catalog design | `catalog-design` | "Configure my Xsolla catalog with gems, gem packs, boosters, regional pricing, and a starter bundle. Then explain how the frontend should read and purchase these items." | Uses Admin API only for setup; uses client Catalog API for storefront; creates VC, VC packages, items, bundle, groups; mentions regional price consistency; verifies schema via MCP/docs; includes order confirmation path; records cleanup. | `>=25%` token reduction; `<=1` clarification; `>=85%` validated confidence; `0` Admin-on-frontend errors. | Uses Admin API in client; passes `country` from storefront; misses cleanup; misses price consistency; ignores order confirmation. |
| Webhooks implementation | `webhooks-impl` | "Implement an Xsolla webhook handler for a headless shop that grants items after purchase. Use Node.js/Express and make signature verification, retries, and duplicate delivery safe." | Reads raw body; computes `lowercase(sha1(rawBody + secret))`; constant-time compare; invalid signature returns `400 INVALID_SIGNATURE`; handles `user_validation`; grants on `order_paid`; idempotent replay; no double grant in separate mode; correct `5xx` retry usage. | `>=25%` token reduction; `0` safety errors; `>=85%` validated confidence; `0` double-grant risks. | Hashes parsed JSON; returns `200` for invalid signature; non-idempotent grant; grants on both `payment` and `order_paid`; uses `5xx` for permanent errors. |
| Full headless shop | `shop-setup` + domain skills | "Create a full sandbox Xsolla headless shop for a mobile F2P game with Login, virtual currency, bundles, embedded checkout, webhook fulfillment, and a simple React storefront." | Uses ready skills; blocks honestly on placeholder skills; does not hallucinate missing Login/payments/store/design guidance; creates phased plan; defines sandbox E2E path. | Use only as integration-level diagnostic until all domain skills are ready. Measure token reduction and clarification count, but do not use as launch pass/fail. | Claims complete production readiness today; invents missing skill content; skips unfinished phases without warning. |

## Excluded Until Skills Exist

| Skill | Why Excluded | What To Measure After Ready |
|---|---|---|
| `login-setup` | Placeholder today. | JWT handoff, widget vs headless auth, cart merge, logout, token storage, Store API Bearer usage. |
| `payments-config` | Placeholder today. | Token method choice, backend/frontend split, Headless Checkout SDK vs Pay Station, sandbox payment flow, Apple Pay / Google Pay constraints. |
| `store-build` | Placeholder today. | React/WordPress storefront implementation, catalog render, cart persistence, checkout handoff, error states. |
| `shop-design` | Placeholder today. | Theme token correctness, supported fields, validation errors, visual consistency, no invented tokens. |

## Data Capture Sheet

| Run ID | Case | Variant | Agent | Model | Tokens To Accept | Clarifications | Manual Corrections | Tool Lookups | Checklist Pass Rate | Safety Errors | Accepted |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| example-001 | catalog-design | AI Kit | Cursor | fixed model | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| example-002 | catalog-design | Baseline | Cursor | fixed model | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Decision Rules

Use AI Kit for a skill when:

- Token reduction is `>=20%`.
- Clarifications are reduced by `>=50%`.
- Validated confidence is `>=85%`.
- Safety errors equal `0`.
- Manual corrections are reduced by `>=50%`.

Do not use AI Kit for a skill when:

- It increases tokens and does not improve validated confidence.
- It causes any safety error.
- It creates false confidence for unfinished areas.
- Baseline performs equally with fewer corrections and lower token cost.

