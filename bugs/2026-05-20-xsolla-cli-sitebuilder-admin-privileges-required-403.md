# xsolla-cli: `sitebuilder enable-preview` and `preview-link` return HTTP 403 `admin_privileges_requred` for verified merchant `ROLE_OWNER` users

- **Tool:** xsolla-cli
- **Version:** v1.8.3 (commit `08c5855`, darwin/arm64, go1.26.1)
- **Affected commands:** `xsolla sitebuilder enable-preview`, `xsolla sitebuilder preview-link` (and likely other write operations under `sitebuilder`)
- **Date observed:** 2026-05-20
- **Reporter:** a.pyanzin@xsolla.com

## Expected result

A user logged into the Publisher Account as the **owner** of a merchant (JWT claim: `partner_data.merchants[0].role == "ROLE_OWNER"`, top-level `is_master == true`) should be able to enable a public preview and fetch its link for any landing under that merchant — both are standard operations exposed in the Publisher Account UI to the same role.

## Actual result

Read operations work; write operations are rejected:

```
$ XSOLLA_SITEBUILDER_SESSION="pa-v4-token=<JWT>" \
    xsolla sitebuilder get-structure \
      --merchant-id 884345 --project-id 306744 --slug unnamed-domain-1a84
→ 200 OK (returns full landing structure)

$ XSOLLA_SITEBUILDER_SESSION="pa-v4-token=<JWT>" \
    xsolla sitebuilder enable-preview --slug unnamed-domain-1a84 --json
{
  "ok": false,
  "error": {
    "code": "http_403",
    "details": {
      "error": {
        "code": "admin_privileges_requred",
        "description": "Occurred an error while verification the authorization token. To perform this action the user must be an admin; token: …; Make sure that you enter correct authorization credentials;"
      }
    }
  }
}

$ XSOLLA_SITEBUILDER_SESSION="pa-v4-token=<JWT>" \
    xsolla sitebuilder preview-link --slug unnamed-domain-1a84 --json
→ same 403 admin_privileges_requred
```

JWT claims (decoded payload of the same `pa-v4-token` used above — value redacted from this file):

```json
{
  "email": "andrey@pyanzin.com",
  "is_master": true,
  "iss": "https://login.xsolla.com",
  "partner_data": {
    "admin": false,
    "merchants": [
      { "id": 884345, "role": "ROLE_OWNER" }
    ]
  },
  "type": "xsolla_login"
}
```

The same JWT is accepted by `sitebuilder get-structure` for the same merchant/landing, so the token, cookie name, and value format are all correct — it is specifically the **role check** that fails.

## Server-side typo

The error code is misspelled: `admin_privileges_requred` (missing "i"). Once this error code is exposed to clients it is effectively a public contract; renaming it later will be a breaking change. Worth fixing now.

## Hypothesis

Site Builder appears to gate write ops on a separate "admin" flag that's distinct from merchant ownership (note `partner_data.admin == false` even though `role == "ROLE_OWNER"` and `is_master == true`). Either:

- the role check should accept `ROLE_OWNER` / `is_master == true` for the merchant whose landing is being modified, or
- the user needs a separate "admin" claim that the README / `publisher login` flow doesn't mention or grant.

Either way, this blocks the documented "make the landing previewable via CLI" workflow for the only user role that can currently obtain a `pa-v4-token` JWT via `publisher login`.

## Repro steps

1. `xsolla publisher login --email <addr>` → succeeds, JWT in Keychain
2. Sign in to https://publisher.xsolla.com in browser, copy `pa-v4-token` cookie value
3. `export XSOLLA_SITEBUILDER_SESSION="pa-v4-token=<JWT>"`
4. Create a sandbox landing in the Publisher Account UI (CLI cannot do this — see [bug 3](./2026-05-20-xsolla-cli-readme-missing-create-website-command.md))
5. `xsolla sitebuilder get-structure --merchant-id 884345 --project-id 306744 --slug <slug>` → 200 OK
6. `xsolla sitebuilder enable-preview --slug <slug> --json` → HTTP 403 `admin_privileges_requred`
7. `xsolla sitebuilder preview-link --slug <slug> --json` → HTTP 403 `admin_privileges_requred`

## Suggested fix

1. **Server:** allow `partner_data.merchants[].role == "ROLE_OWNER"` (or `is_master == true`) to satisfy the admin gate when the landing belongs to that merchant.
2. **Server:** fix the typo `requred` → `required` in the error code now, before more clients pin to it.
3. **CLI:** when the server returns `admin_privileges_requred`, the CLI could surface a clearer hint — e.g. "your session token is for a non-admin role; site preview requires a Publisher Account admin" — instead of dumping the raw token in the error message (which it currently does, see "description" above; this also leaks the JWT into terminal scrollback / log files).

## Related bugs in this folder

- [`2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md`](./2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md) — env-var name, cookie name, and value format are all undocumented incorrectly. This bug only became debuggable after the auth format above was figured out.
- [`2026-05-20-xsolla-cli-readme-missing-create-website-command.md`](./2026-05-20-xsolla-cli-readme-missing-create-website-command.md) — `webshop create-website` does not exist; landings must be created in the UI first.
