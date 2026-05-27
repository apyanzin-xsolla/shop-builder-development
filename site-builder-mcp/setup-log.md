# site-builder-mcp setup log

Source: Slack thread in #C09JXCKGF9N (2026-05-26), instructions from Egor Solodaev.

Goal: install `@site-builder/mcp-server` from the private GitLab npm registry
(project 659 on gitlab.loc) and wire it up to Claude Code.

---

## Step 1 — Create folder

- 2026-05-26 — `mkdir -p /Users/a.pyanzin/shop-builder-development/site-builder-mcp`
- Result: folder created, empty.

## Step 2 — Initialize log

- 2026-05-26 — Created this file.

## Step 3 — `npm init -y`

- 2026-05-26 — Ran `npm init -y` in folder.
- Result: package.json created (name=site-builder-mcp, version=1.0.0, type=commonjs).

## Step 4 — Write `.npmrc`

- 2026-05-26 — Wrote `.npmrc` in the folder with `@site-builder` registry, GitLab token (`glpat-...`), and `strict-ssl = false`.

## Step 5 — Verify with `npm info @site-builder/mcp-server`

- 2026-05-26 — Ran from the folder. Success:
  `@site-builder/mcp-server@0.0.1-beta14 | Proprietary | deps: 6 | versions: 8`
  Registry access confirmed.

## Step 6 — Write `.mcp.json`

- 2026-05-26 — Wrote `.mcp.json` (with leading dot, which is what Claude Code reads — Egor's snippet called it `mcp.json`).
- Fixed two JSON typos in Egor's snippet: missing comma after `"APP_ENV": "production"`, trailing comma after the inner `}`.
- `SB_SERVER_TOKEN` is a JWT for user `andrey@pyanzin.com`, merchant 884345 (ROLE_OWNER), issuer `login.xsolla.com`.
- **Expires 2026-06-05** (10 days from setup). Refresh required after that.

## Step 7 — Register with Claude Code

- Decision: **Option 1 — folder-isolated**. `.mcp.json` and `.npmrc` both live in `site-builder-mcp/`. Server is loaded only when Claude Code is launched from this folder.
- Reasoning:
  - Matches Egor's documented instructions.
  - Keeps SB_SERVER_TOKEN + GitLab token contained.
  - `strict-ssl = false` does not leak to global npm.
- Boot test (2026-05-26): ran `npx -y @site-builder/mcp-server@latest` from the folder. Process started successfully:
  - stderr: `Site Builder MCP Server running on stdio` (normal — MCP servers log to stderr, use stdout for JSON-RPC).
  - No crash, no token-validation error.
- Confirmed no global `~/.npmrc` exists, so registry/token config is exclusively local to this folder.

## How to use

1. Open a new terminal.
2. `cd /Users/a.pyanzin/shop-builder-development/site-builder-mcp/`
3. Run `claude` to start a Claude Code session in that folder.
4. Approve loading `.mcp.json` when prompted.
5. Run `/mcp` to confirm `site-builder-mcp` is connected.

## Maintenance reminders

- **SB_SERVER_TOKEN expires 2026-06-05** (~10 days). Get a new one from Publisher Account and replace the value in `.mcp.json`.
- GitLab `glpat-` token in `.npmrc` has its own expiry (whatever you set when generating it in GitLab → User Settings → Access Tokens).
- Token rotation: both tokens were pasted in chat during setup — rotate if that's a concern.

---

## Errors encountered

1. **`timeout` not found** during boot test on macOS — used `&` + `sleep` + `kill` instead. Not an MCP issue; just a test-script issue.
2. **Initial confusion about Confluence page** — user-provided link (`x/LQCZvAU`, "Specs from MCP" page) is the API spec, not the installation guide. Did not contain SB_SERVER_TOKEN generation steps. User provided the token directly instead.


---

## Errors encountered

(none yet)

---

## MCP vs. Site Builder REST API — coverage comparison

**What this table is:** a side-by-side map between the tools exposed by the `site-builder-mcp` MCP server and the REST endpoints documented in the "Specs from MCP" Confluence page (https://xsolla.atlassian.net/wiki/x/LQCZvAU, fetched 2026-05-26). Each row lists an MCP tool, the API endpoint(s) it most likely wraps, and a match indicator: ✅ direct match in the doc, ❓ no direct match (tool may wrap an undocumented endpoint, derive data client-side, or compose multiple calls). The second part of the section lists endpoints that exist in the API doc but are **not** exposed by the MCP — i.e., gaps in MCP coverage.

Purpose: quickly see what you can do via this MCP today vs. what would require calling the REST API directly (or extending the MCP).

### Mapping: MCP tool → API endpoint

| MCP tool | API endpoint(s) it most likely wraps | Match |
|---|---|---|
| `list_sites` | `GET /merchant/{m}/project/{p}/landings` | ✅ |
| `get_site` | `GET /merchant/{m}/project/{p}/landing/{domain}` | ✅ |
| `get_site_stats` | *(no direct match in doc)* | ❓ |
| `list_pages` | `GET .../landing/{domain}/pages` | ✅ |
| `get_page` | `GET .../landing/{domain}/pages/{pageId}` | ✅ |
| `list_blocks` | `GET .../landing/{domain}/structure` (likely) | ✅ |
| `list_block_modules` | `GET .../ui/{landing}/components` | ✅ |
| `list_federated_blocks` | *(no direct match)* | ❓ |
| `search_blocks` | *(no direct match — likely client-side filter over `components`)* | ❓ |
| `get_block` | `GET .../landing/{domain}/blocks/{blockId}` | ✅ |
| `get_block_schema` | *(not in doc — possibly derived from components)* | ❓ |
| `create_block_via_api` | `POST .../ui/{landing}/page/{pageId}/block` | ✅ |
| `update_block` | `PUT .../ui/{landing}/saveblock` | ✅ |
| `delete_block` | `DELETE .../landing/{domain}/blocks/{blockId}` or `DELETE .../ui/{landing}/page/{pageId}/block` | ✅ |
| `create_sidebar` | *(no exact endpoint — likely wraps block-create with sidebar type)* | ❓ |
| `get_block_translations` | `GET .../landing/{domain}/linking` | ✅ |
| `update_localization` | `POST .../landing/{domain}/linking` and/or `POST /localization/update/{domain}` | ✅ |
| `create_ai_block` | `POST .../ai-custom-block` | ✅ |
| `get_ai_block_source` | `GET .../ai-custom-block/{id}` (+ `/remoteEntry.js`) | ✅ |
| `update_ai_block` | `PUT .../ai-custom-block/{id}` | ✅ |
| `delete_ai_block` | `DELETE .../ai-custom-block/{id}` | ✅ |
| `say_hello` | utility — no API call | — |

**Coverage:** ~15 documented endpoints out of ~100+ are wrapped by the MCP. Roughly 85% of the documented API surface is **not** exposed.

### Gaps — documented in the API but not in the MCP

**Site lifecycle**
- `POST .../landing/{domain}` — create site
- `PATCH .../landing/{domain}` — rename / domain change
- `DELETE .../landing/{domain}` — delete site
- `POST .../landing/{domain}/duplicate` — duplicate site
- `POST .../landing/{domain}/publication` — publish
- `GET .../landing/{domain}/check` — pre-publish check
- `GET|PUT .../landing/{domain}/versions[/{id}]` — version history & rollback
- `PATCH .../landing/{domain}/features` — feature flags
- `PATCH|DELETE .../landing/{domain}/restrictions` — access restrictions
- `POST .../landing/{domain}/template`, `POST .../landing/{domain}/portal` — templates / portal
- `GET .../landing/{domain}/theme` — theme CSS
- `GET|POST .../landing/{domain}/structure` — site structure

**Pages**
- No `create_page`, `update_page`, `delete_page`, `duplicate_page` exposed (these exist on the email-customization side: `POST|PATCH|DELETE .../next-customization/email/{type}`)

**Blocks**
- `PUT .../ui/{landing}/page/{pageId}/block` — **move** block
- `POST .../ui/{landing}/page/{pageId}/block/duplicate` — **duplicate** block
- `POST .../ui/{landing}/page/{pageId}/block/changeVersion` — **change block version**
- `PUT .../ui/{landing}/page/{pageId}/savepagesettings` — page settings
- `PUT .../ui/{landing}/savelandingsettings` — landing settings

**Domains / languages**
- `POST|PATCH|DELETE .../landing/{domain}/domains` — external domain CRUD
- `GET .../landing/{domain}/domains/lookup` — DNS check
- `POST|DELETE .../landing/{domain}/language` — add/remove locales

**Connectors / integrations**
- `PUT|DELETE .../landing/{domain}/applications` — connector config
- `GET .../landing/{domain}/parsing` — third-party data
- `PUT .../landing/{domain}/store-api-retry`

**Store / catalog lookups (UI helpers)**
- `/ui/{landing}/sku`, `/store/games`, `/store/virtualItems`, `/store/virtual_currency[/package]`, `/store/{group_id}`, `/subscriptionPlans`, `/launcherList`

**Assets**
- All four asset endpoints (`GET|POST|PATCH|DELETE .../assets/...`)

**Customization (emails + general)**
- Entire `customization` and `next-customization` namespaces (~15 endpoints)

**Login**
- Entire `/login/projects`, `/login/configuration/{id}`, `/login/widget-customization/{id}` namespaces

**API Keys**
- `list`, `create`, `revoke`, `change-scopes`, `validate`

**Preview / session / tokens**
- `GET /preview/{domain}/{page}/{locale}`
- `GET .../public-preview/...` (enable, disable, link)
- `POST /session[/{domain}]`
- `POST .../token/order`

**Admin / ops**
- `POST|DELETE /dev-mode/{merchantId}`
- `GET /healthcheck`, `/healthcheck/client`, `/healthcheck/third-party`
- `GET|POST|PUT|DELETE /site-template`, `POST /site-template/sync`
- `PUT .../landing/{domain}/admin/change-landing-type|change-merchant|change-project`

**Misc**
- `GET /merchant/merchants/{m}/agreements`
- `GET /merchant/{m}/projects/list`
- `GET /partner/gotc/prices`
- `GET /airtable`, `GET /link`
- `GET|DELETE /user-information` (GDPR)
- `PUT /landing/{domain}/google-shopping`
