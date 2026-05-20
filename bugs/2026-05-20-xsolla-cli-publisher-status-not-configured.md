# xsolla-cli: `publisher status` / `list-projects` / `list-api-keys` falsely report "not configured"

- **Tool:** xsolla-cli
- **Version:** v1.8.3 (commit `08c5855`, darwin/arm64, go1.26.1)
- **Binary path:** `~/.local/bin/xsolla`
- **Config path:** `~/.xsolla.json` (`default_environment: "dev"`, `merchant_id` + `project_id` populated)
- **Date observed:** 2026-05-20
- **Reporter:** a.pyanzin@xsolla.com

## Expected result

Per README (lines 242–252), after `xsolla publisher login` the JWT is stored in the OS keychain and "used automatically by profile, api-keys, and projects commands". So `xsolla publisher status`, `list-projects`, and `list-api-keys` should work without further setup.

## Actual result

After successful `xsolla publisher login`:

| Command | Result |
|---|---|
| `xsolla auth status` | Logged in ✅ |
| `xsolla publisher get-profile` | returns profile ✅ |
| `xsolla catalog list-items --project-id <id>` | real API call works ✅ |
| `xsolla publisher status` | ❌ `not configured — run 'xsolla publisher signup' first` |
| `xsolla publisher list-projects` | ❌ same error |
| `xsolla publisher list-api-keys` | ❌ same error |

Trace log shows both JWT and API key load from keychain, yet the command exits with "not configured":

```
[DEBUG] Loaded bearer token from keychain for profile "default"
[DEBUG] Loaded API key from keychain for profile "default"
not configured — run 'xsolla publisher signup' first
```

`--environment dev` and renaming the env to `default` in `~/.xsolla.json` do not help.

## What is incorrect in the README

The README documents `publisher status` / `list-projects` / `list-api-keys` as working after `publisher login`, but they don't — they error out telling the user to run `signup`, which the README itself says is only for *new* accounts. Either the commands are broken, or the README needs to document a missing prerequisite. The error message ("run signup first") is also misleading for already-registered users following the documented login flow.

## Repro steps

1. `xsolla publisher login --email <addr>` → succeeds (JWT in Keychain)
2. `xsolla auth status` → "Logged in (profile: default)" ✅
3. `xsolla publisher get-profile` → returns profile ✅
4. `xsolla config list` → shows `merchant_id`, `project_id` correctly ✅
5. `xsolla catalog list-items --project-id <id>` → real API call works ✅
6. `xsolla publisher status` → fails with "not configured"
7. `xsolla publisher list-projects` → fails with "not configured"
8. `xsolla publisher list-api-keys` → fails with "not configured"
