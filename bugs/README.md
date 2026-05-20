# xsolla-cli — Bug Log

Tracked bugs and command-by-command pass/fail outcomes for the `xsolla` CLI, while building a test Shop Builder storefront for the game *Three in a Row: Orchard*.

**Environment for all entries below:**
- xsolla-cli `v1.8.3` (commit `08c5855`, darwin/arm64, go1.26.1)
- merchant `884345`, project `306744` (sandbox)
- reporter: `a.pyanzin@xsolla.com`

---

## Open bugs

| # | Title | File |
|---|---|---|
| 1 | `publisher status` / `list-projects` / `list-api-keys` / `create-project` falsely report "not configured" — workflow blocker | [`2026-05-20-xsolla-cli-publisher-status-not-configured.md`](./2026-05-20-xsolla-cli-publisher-status-not-configured.md) |
| 2 | Site Builder session-cookie auth: wrong env-var name, wrong cookie name, wrong value format — all three docs are inconsistent | [`2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md`](./2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md) |
| 3 | `webshop create-website` / `update-website-theme` documented in README but do not exist in v1.8.3 | [`2026-05-20-xsolla-cli-readme-missing-create-website-command.md`](./2026-05-20-xsolla-cli-readme-missing-create-website-command.md) |
| 4 | `xsolla update` 404s on the private GitHub repo — no auth path | [`2026-05-20-xsolla-cli-update-private-repo-404.md`](./2026-05-20-xsolla-cli-update-private-repo-404.md) |
| 5 | `sitebuilder enable-preview` / `preview-link` HTTP 403 `admin_privileges_requred` for verified `ROLE_OWNER` users (+ server-side typo) | [`2026-05-20-xsolla-cli-sitebuilder-admin-privileges-required-403.md`](./2026-05-20-xsolla-cli-sitebuilder-admin-privileges-required-403.md) |

---

## Commands run in the 2026-05-20 session

| # | Command | Status | Notes |
|---|---|---|---|
| **Install / GitHub auth** | | | |
| 1 | `brew install gh` | ❌ | Homebrew not installed on host |
| 2 | `curl ... gh release / unzip / install ~/.local/bin/gh` | ✅ | Manual install workaround |
| 3 | `gh auth login --web` | ✅ | Logged in as `apyanzin-xsolla` |
| 4 | `gh repo view xsolla/xsolla-cli` | ✅ | Authenticated read of private repo |
| 5 | xsolla-cli `install.sh` (piped from API) | ❌ | `jq` parse error, then 404 on release-asset download |
| 6 | `gh release download v1.8.3 ... darwin_arm64.tar.gz` | ✅ | Workaround to install xsolla CLI |
| **xsolla CLI — basic** | | | |
| 7 | `xsolla version` | ✅ | Reports v1.8.3 |
| 8 | `xsolla --help` | ✅ | |
| 9 | `xsolla update --check` | ❌ | GitHub 404 — **bug 4** |
| **xsolla — auth / publisher** | | | |
| 10 | `xsolla publisher login --email <addr>` | ✅ | Run interactively with `!` |
| 11 | `xsolla publisher status` | ❌ | "not configured" — **bug 1** |
| 12 | `xsolla publisher get-profile` | ✅ | Returns profile, confirms JWT works |
| 13 | `xsolla publisher list-projects` | ❌ | "not configured" — **bug 1** |
| 14 | `xsolla publisher list-api-keys` | ❌ | "not configured" — **bug 1** |
| 15 | `xsolla publisher create-api-key` | ✅ | Run interactively with `!` |
| 16 | `xsolla publisher create-project` | ❌ | "not configured" — **bug 1** (workflow blocker) |
| 17 | `xsolla merchant create-projects` | ❌ | HTTP 401 — Basic-Auth fallback also blocked |
| 18 | `xsolla auth status` | ✅ | Confirms login |
| **xsolla — config** | | | |
| 19 | `xsolla config list` | ✅ | Shows merchant / project / sandbox flag |
| 20 | `xsolla config get merchant_id` / `project_id` | ✅ | |
| **xsolla — catalog (read)** | | | |
| 21 | `xsolla catalog list-items --project-id 306744` | ✅ | Lists 7 items |
| 22 | `xsolla catalog list-items --project-id 306961` | ❌ | HTTP 401 — API key not scoped to that project |
| 23 | `xsolla catalog list-bundles --project-id 306744` | ✅ | Lists 1 bundle |
| 24 | `xsolla catalog list-currency ...` | ❌ | User error — subcommand does not exist (real names: `list-admin-currency` / `list-catalog-currency`). Worth flagging the misleading error message ("unknown flag: --project-id") that hides the real cause. |
| **xsolla — catalog (writes)** | | | |
| 25 | `xsolla catalog create-admin-currency` (Sunbeams) | ✅ | item id `1417379` |
| 26 | `xsolla catalog create-admin-currency-package` × 5 | ✅ | item ids `1417380`–`1417384` |
| 27 | `xsolla catalog create-items` × 7 (boosters + lives) | ✅ | item ids `1417385`–`1417391` |
| 28 | `xsolla catalog create-admin-bundles` (starter pack) | ✅ | item id `1417392` |
| **xsolla — webshop / sitebuilder** | | | |
| 29 | `xsolla webshop create-website` | ❌ | Subcommand does not exist — **bug 3** |
| 30 | `xsolla sitebuilder get-structure` (with correct env-var + cookie format) | ✅ | Returned full landing structure |
| 31 | `xsolla sitebuilder enable-preview` | ❌ | HTTP 403 `admin_privileges_requred` — **bug 5** |
| 32 | `xsolla sitebuilder preview-link` | ❌ | HTTP 403 `admin_privileges_requred` — **bug 5** |

### Tally

- ✅ **17 passes** (14 of them catalog writes)
- ❌ **15 failures** (5 tracked as bugs, 4 environmental / install-related, 1 user typo with misleading error message)

---

## Bug-filing convention used in this folder

- File naming: `YYYY-MM-DD-xsolla-cli-<short-summary>.md`
- Each file includes: Tool / Version / Affected command(s) / Date / Reporter / Expected / Actual / What is incorrect / Repro steps / Suggested fix / Related bugs
- This `README.md` is the index — update both this file and the new file when adding a bug
