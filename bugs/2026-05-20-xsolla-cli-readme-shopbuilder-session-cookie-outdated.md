# xsolla-cli: Site Builder session-cookie auth is undocumented correctly — wrong env-var name in README, wrong cookie name, wrong value format

- **Tool:** xsolla-cli
- **Version:** v1.8.3 (commit `08c5855`, darwin/arm64, go1.26.1)
- **Affected docs:** `README.md` — "Create a Shop Builder Web Shop Website" section, and `xsolla --help` ("Environment Variables" block)
- **Date observed:** 2026-05-20
- **Reporter:** a.pyanzin@xsolla.com

## Expected result

The README instructs the user to set the `XSOLLA_SHOPBUILDER_SESSION` env var using the `ps2[user_session]` cookie from their Publisher Account browser session:

```
export XSOLLA_SHOPBUILDER_SESSION="your-ps2-user-session-cookie"
```

The CLI's own `--help` output reinforces this:

```
XSOLLA_SITEBUILDER_SESSION
   Publisher Account ps2[user_session] cookie value for
   Site Builder webshop workflows.
```

User opens DevTools on `https://publisher.xsolla.com`, finds `ps2[user_session]`, copies its value, and runs `xsolla webshop create-website`.

## Actual result

`ps2[user_session]` **does not exist** in the cookies for `publisher.xsolla.com` (or any `.xsolla.com` subdomain) in a current Publisher Account session. Verified in Chromium DevTools → Application → Cookies for both `publisher.xsolla.com` and `.xsolla.com` parent domain.

Cookies present (relevant ones, all on `.xsolla.com`):

| Name | Looks like |
|---|---|
| `pa-v4-token` | JWT (`eyJhbGciOiJ...`) — likely the modern session token |
| `pa-merchant-id` | Numeric merchant ID |
| `pa-locale` | locale string |
| `pa_visit` | flag |
| `sb-pa-merchant-id` | Numeric merchant ID (Shop Builder context) |
| `sb-pa-project-id` | Numeric project ID (Shop Builder context) |
| `sb-pa-locale` | locale string |
| `gc-pa-v4-token` | another JWT |
| `gc-pa-merchant-id` | Numeric merchant ID |
| `JSESSIONID` | Tomcat-style session ID on `publisher.xsolla.com` |

No cookie named `ps2[*]` or containing `user_session` exists. The session/auth model appears to have been migrated to a JWT-based scheme (`pa-v4-token` family) since the README was written.

## What is incorrect in the README

1. **`ps2[user_session]` is named but no longer exists.** Users who follow the README literally will fail to find the cookie.
2. The error mode is silent — the user doesn't get any "this cookie name is outdated" hint, just confusion.
3. The same wording is duplicated in `xsolla --help` ("Environment Variables" section) — both places need updating.
4. The README should either name the correct cookie (`pa-v4-token`, `sb-pa-v4-token`, or whatever the CLI actually accepts) or — preferably — document an auth path that doesn't require pasting a raw browser cookie at all (e.g. reuse the JWT already stored in the OS keychain by `publisher login`).

## Update 2026-05-20 — actual working format found

After experimenting, the auth env var is accepted with **all three** of these things different from what the docs say:

| Thing | README / main `xsolla --help` says | What actually works |
|---|---|---|
| Env-var name | `XSOLLA_SHOPBUILDER_SESSION` | `XSOLLA_SITEBUILDER_SESSION` |
| Cookie name | `ps2[user_session]` | `pa-v4-token` (the modern session JWT cookie on `.xsolla.com`) |
| Value format | bare value, e.g. `your-ps2-user-session-cookie` | full `name=value` pair, e.g. `pa-v4-token=<JWT>` |

The internal subcommand help (e.g. `xsolla sitebuilder get-structure --help`) at least uses the correct env-var name `XSOLLA_SITEBUILDER_SESSION` — but still tells the user to set it to `ps2[user_session]=...`, which doesn't exist either. So even within the CLI's own help text the documentation is inconsistent.

### Test matrix (run against the live `unnamed-domain-1a84` landing under merchant 884345)

```
XSOLLA_SITEBUILDER_SESSION="pa-v4-token=$JWT"      sitebuilder get-structure   → 200 OK ✅
XSOLLA_SITEBUILDER_SESSION="$JWT"                  sitebuilder get-structure   → HTTP 403 ❌
XSOLLA_SITEBUILDER_SESSION="ps2[user_session]=…"   sitebuilder get-structure   → HTTP 403 ❌
XSOLLA_SHOPBUILDER_SESSION="pa-v4-token=$JWT"      sitebuilder get-structure   → "XSOLLA_SITEBUILDER_SESSION is required" ❌
```

### Suggested fix (combined)

- **README:** update the example to `XSOLLA_SITEBUILDER_SESSION="pa-v4-token=<token>"` (or whatever the canonical cookie name is).
- **`xsolla --help` "Environment Variables":** rename `XSOLLA_SHOPBUILDER_SESSION` → `XSOLLA_SITEBUILDER_SESSION` and update its description.
- **Subcommand help (`sitebuilder get-structure --help`, `enable-preview --help`, etc.):** update the inline "How to obtain it" snippet to point at `pa-v4-token` (or, again, just reuse the JWT in Keychain).

## Repro steps

1. `xsolla publisher login --email <addr>` → succeeds, JWT in keychain
2. Open https://publisher.xsolla.com in a logged-in browser
3. DevTools → Application → Cookies → look for `ps2[user_session]`
4. Result: no such cookie exists; closest matches are `pa-v4-token` and `sb-pa-*` family
5. README-recommended setup cannot be completed as written

## Suggested fix

- Update README "Create a Shop Builder Web Shop Website" section to name the actual cookie used by the current CLI.
- Update the `xsolla --help` `XSOLLA_SITEBUILDER_SESSION` description likewise.
- Long-term: avoid requiring a raw browser cookie at all — let `webshop create-website` use the JWT already stored in OS Keychain by `publisher login`, the same way `publisher get-profile` does.
