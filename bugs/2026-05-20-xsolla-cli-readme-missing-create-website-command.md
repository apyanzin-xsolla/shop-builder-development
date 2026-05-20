# xsolla-cli: README documents `webshop create-website` / `webshop update-website-theme` but they do not exist in v1.8.3

- **Tool:** xsolla-cli
- **Version:** v1.8.3 (commit `08c5855`, darwin/arm64, go1.26.1)
- **Affected docs:** `README.md` — "Create a Shop Builder Web Shop Website" section (Quick Start step 4)
- **Date observed:** 2026-05-20
- **Reporter:** a.pyanzin@xsolla.com

## Expected result

Per the README, the user can create a Shop Builder webshop website directly from the CLI:

```bash
export XSOLLA_SHOPBUILDER_SESSION="your-ps2-user-session-cookie"

xsolla webshop create-website \
  --merchant-id 878658 \
  --project-id 304523 \
  --name "My Web Shop" \
  --parse-target "https://play.google.com/store/apps/details?id=com.example.game" \
  --accent-color "rgba(255, 0, 91, 1)" \
  --button-border-radius 21 \
  --json
```

And update an existing one's theme:

```bash
xsolla webshop update-website-theme \
  --merchant-id 878742 \
  --project-id 304577 \
  --slug my-web-shop \
  --primary-color "#2D5BFF" \
  --accent-color "#00AA44" \
  --button-border-radius 12 \
  --json
```

## Actual result

Neither command exists in v1.8.3. Running them returns a misleading error because the parser falls back to the parent `webshop` group:

```
$ xsolla webshop create-website --merchant-id 884345 --project-id 306744 ...
unknown flag: --merchant-id
```

`xsolla webshop --help` lists only cart / order / payment / grant subcommands — no website management at all:

```
Available Commands:
  add-cart-item, add-current-cart-item, buy-virtual-item,
  clear-cart, clear-cart-by-id, create-admin-payment-token,
  create-order-cart, create-order-cart-by-id, create-order-item,
  fill-admin-cart, fill-admin-cart-by-id, fill-cart, fill-cart-by-id,
  get-cart, get-cart-by-id, get-order, grant-free-cart,
  grant-free-cart-by-id, grant-free-item, init-widget,
  remove-cart-item, remove-current-cart-item, search-orders
```

`xsolla sitebuilder --help` also has no `create-website`. Sitebuilder offers only management of already-existing landings (`add-domain`, `add-language`, `apply-version`, `duplicate-website`, `enable-preview`, `verify-website`, etc.).

**Net effect:** there is no CLI path to create a new webshop site in v1.8.3. Users following the README's Quick Start step 4 are blocked and must fall back to the Publisher Account web UI.

## What is incorrect in the README

1. The README documents `xsolla webshop create-website` as if it exists — it does not.
2. The README documents `xsolla webshop update-website-theme` likewise — it does not.
3. The accompanying `XSOLLA_SHOPBUILDER_SESSION` env var instruction is dead-code without these commands.
4. The error users see (`unknown flag: --merchant-id`) does not hint at the real cause (missing subcommand), making the failure mode hard to debug.

## Repro steps

1. `xsolla --version` → `1.8.3`
2. `export XSOLLA_SHOPBUILDER_SESSION="<valid-token>"`
3. `xsolla webshop create-website --merchant-id 884345 --project-id 306744 --name "Three in a Row: Orchard" --accent-color "rgba(252, 165, 60, 1)" --button-border-radius 16 --json`
4. Result: `unknown flag: --merchant-id`
5. `xsolla webshop --help` confirms no `create-website` / `update-website-theme` exist.
6. `xsolla sitebuilder --help` confirms no equivalent exists there either.

## Suggested fix

Either:

- **Ship the commands** — implement `webshop create-website` and `webshop update-website-theme` (or the equivalent under `sitebuilder`), keeping the README accurate. Ideally, accept auth via the JWT already stored in Keychain (the one issued by `publisher login`), so users don't need to copy a browser cookie at all.
- **Or update the README** — remove or clearly mark the entire "Create a Shop Builder Web Shop Website" section as unimplemented in v1.8.3, and direct users to the Publisher Account UI for site creation in the meantime.

## Related bugs in this folder

- [`2026-05-20-xsolla-cli-publisher-status-not-configured.md`](./2026-05-20-xsolla-cli-publisher-status-not-configured.md) — `publisher status` / `list-projects` / `list-api-keys` / `create-project` false negative
- [`2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md`](./2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md) — README points to non-existent `ps2[user_session]` cookie
