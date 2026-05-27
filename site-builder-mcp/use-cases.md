# Site Builder MCP — use case tests

Purpose: exercise the `site-builder-mcp` server against real business prompts and
record what works, what fails, and which gaps in MCP coverage block each case.

Scope: the publisher account wired up via `.mcp.json` (merchant 884345, token
issued to andrey@pyanzin.com, expires 2026-06-05). Single existing site
`unnamed-domain-b146` (project 306961), `type: "topup"`.

Source of prompts: Confluence — *Test Prompts for Shop Builder MCP*
(`/wiki/spaces/shpb/pages/24553161189`), pulled 2026-05-26.

Run targets:
- Page `Hamster Tap Tap` (`/hamster-tap-tap`, pageId
  `6a09ff0dded173de5678f2f6`) — used for the initial run on 2026-05-26.
  All test blocks created there were later deleted by user request.
- Page `mcp-test` (`/mcp-test`, pageId `6a15dc82397bda3c0dedd788`,
  `type: "blank"`, created by user via Publisher UI) — second run on
  2026-05-26 to validate creates from a clean slate. Block IDs recorded
  under "mcp-test run" in each test below.

The MCP cannot create a new page (no `create_page` tool), so the empty page
had to be created in the Publisher UI before the second run.

Known constraint up front: the MCP does **not** expose `create_site` /
`create_project`. Anything requiring a brand-new site has to be created outside
the MCP (UI or direct REST). See `setup-log.md` → "MCP vs. Site Builder REST API
— coverage comparison" for the full gap list.

Tools available in this MCP (from the schema set used here):
`create_ai_block`, `update_ai_block`, `delete_ai_block`, `get_ai_block_source`,
`create_block_via_api`, `create_sidebar`, `delete_block`, `get_block`,
`get_block_schema`, `get_block_translations`, `update_block`,
`update_localization`, `get_page`, `list_pages`, `get_site`, `get_site_stats`,
`list_sites`, `list_block_modules`, `list_blocks`, `list_federated_blocks`,
`search_blocks`, `say_hello`.

No tools for: site create, template switch, publish/unpublish, custom domain,
whitelist/restrictions, theme/site-level config update (`update_site`),
analytics integration, page-level config update (`update_page`), block reorder
(`move_block`), or version rollback.

---

## How each test is recorded

For every prompt:

```
### Test N — <short title>

**Prompt (verbatim):**
> ...

**Goal:** what the user expected to happen.

**MCP tools used:** list_sites, create_block_via_api, ...

**Steps & results:**
1. ...
2. ...

**Outcome:** ✅ success / ⚠️ partial / ❌ blocked

**If blocked — what blocked it:** missing tool / missing arg / API error / auth / other.

**Workaround / next step:** ...
```

---

## Tests

### Test 1 — Web Shop template + Store block for game keys

**Prompt (verbatim):**
> I'm building a site on the Web Shop template. Add a Store block and configure
> it to sell game keys. If something is wrong with this, explain why and suggest
> alternatives.

**Goal:** add a Store block to a "Web Shop" template site with item type set to
game keys; MCP should also recognise template/item mismatches and flag them.

**MCP tools used:** `get_site`, `list_block_modules`, `get_block_schema`
(`newStore`), `search_blocks`, `get_block`.

**Steps & results:**
1. `get_site` on the only site we have → `type: "topup"`, not `"web-shop"`. The
   MCP has no concept of "Web Shop template" in its responses, and exposes no
   tool to change the template.
2. `list_block_modules` confirms `newStore` is the canonical Store block
   (`store` is marked deprecated).
3. `get_block_schema newStore` returns `section.item.type` enum =
   `BUNDLE | UNIT | VIRTUAL_CURRENCY | VIRTUAL_GOOD | UPSELL`. No `GAME_KEYS`
   value. No hint that game keys map to UNIT or any other type.
4. `get_block` on an existing newStore reveals a `card.layouts.game-keys-vertical`
   layout (with `releaseDate`, `gameKeyPlatform` flags) — proving game keys are
   supported in rendering — but **none** of those layout fields appear in the
   schema returned by `get_block_schema`.

**Outcome:** ⚠️ partial — block creatable and renderable on the second
attempt (only after I supplied the `card` defaults the schema didn't tell me
about); MCP still can't reach "game keys" semantically.

**First attempt (Hamster Tap Tap, now deleted):** `create_block_via_api` with
section `{ item: { type: "UNIT", group: "__all__" }, title: "Game Keys" }` —
no `card` field. Server returned `created: true`. Editor crashed with
`Failed to render block newStore — Cannot read properties of undefined
(reading 'selectedLayoutType')`. Block deleted to restore the editor.

**mcp-test run:** `create_block_via_api` with the same section *plus* a full
`card: { selectedLayoutType: "game-keys-vertical", layouts: {...} }` object
copied from an existing newStore. Returned
`blockId: 6a15dd0e5de2b1d331c01443`; renders without crashing.

**The new bug from this:** `create_block_via_api newStore` does not apply
`card` defaults to API-created `newStoreSection` components. Server should
either inject defaults or reject the request — currently it does neither,
which is how a 200 response becomes a renderer crash.

**What I still couldn't reach:**
- No template-awareness (`get_site.type` is `"topup"`, not "Web Shop").
- `get_block_schema newStore` doesn't expose `card.layouts.*`, so a model
  driving the MCP can't pick `game-keys-vertical` without copying it from an
  existing block.

**What I couldn't reach:**
- No template-awareness in the MCP. There is no way to ask "is this site a Web
  Shop?" except by guessing from `type` (`"topup"`, `"web-shop"`, `"sellingpage"`
  appear in payloads), and no way to switch.
- `newStore` schema doesn't expose the "game keys" item type or the
  `game-keys-vertical` card layout. The block clearly supports it at runtime
  (visible in `get_block` payloads), but the MCP schema lies by omission. A
  model following only the schema would default to UNIT/VIRTUAL_GOOD and
  silently miss the dedicated layout.
- No way to validate "wrong template ↔ wrong block" from MCP data alone.

**Workaround / next step:** extend `get_block_schema` to expose `card.layouts`
(including `game-keys-vertical`) and add an explicit `GAME_KEYS` (or document
the UNIT+layout combo). Add a `template` / `siteType` field on `list_sites` /
`get_site` responses and document allowed block ↔ template combinations.

---

### Test 2 — List blocks for site, restrictions per block

**Prompt (verbatim):**
> List all blocks I can add on a site created. For each, tell me if there are
> restrictions (content-only vs full edit). Which ones makes sense to my case?

**Goal:** enumerate creatable blocks for *this* site with per-block
edit-restriction metadata.

**MCP tools used:** `list_block_modules`, `list_federated_blocks`,
`get_site`.

**Steps & results:**
1. `list_block_modules` returns three groups: `native` (23 modules incl. hero,
   newStore, lead, faq, footer, …), `federated` (4: sb-offer-chain,
   sb-daily-reward, social-quests, offerwall-block), and `cannotCreate` (header,
   common-layout, side-by-side-layout, sidebar, deprecated `store`).
2. `list_federated_blocks` returns id/name/version/host but nothing about edit
   restrictions.
3. There is **no** field in any response indicating "content-only" vs
   "full-edit" vs "structural-only" — neither per block, per template, nor per
   subscription tier.
4. "Which makes sense to my case?" requires knowing the site's vertical /
   template; `get_site.type` returns `"topup"` but there is no catalogue
   mapping templates → recommended blocks.

**Outcome:** ⚠️ partial (the list comes back; the restriction & recommendation
metadata does not).

**If blocked — what blocked it:** missing fields on `list_block_modules` /
`list_federated_blocks` (no `editScope`, `allowedTemplates`, `recommendedFor`).

**Workaround / next step:** enrich `list_block_modules` with `editScope`
(`content-only` / `style` / `full`) and `availableOn` (template list) for every
module. Add a `recommend_blocks(siteId)` tool that filters by template.

---

### Test 3 — Cross-template behavior (Store / Login / Cart)

**Prompt (verbatim):**
> What's the difference in how the Store block behaves on a Web Shop template
> vs an Single game page template? List concrete behavioral differences, not
> just visual ones. Do the same for login methods and shopping cart.

**Goal:** behavioral diff (not just style) of the same block/feature across
two templates.

**MCP tools used:** `list_block_modules`, `get_block_schema` (`newStore`,
`fast-login`), `get_site`.

**Steps & results:**
1. `get_block_schema` is identical regardless of which template the caller
   intends to use — the schema endpoint takes only `module`, not `template`.
2. `list_block_modules` doesn't tag any module as "behaves differently on X".
3. There is no `get_template` or `list_templates` tool. Template identity is
   only inferable from `site.type` strings (`topup`, `sellingpage`, …) without
   any documented mapping to behavior.

**Outcome:** ❌ blocked.

**If blocked — what blocked it:** no template catalogue and no
template-conditioned schema.

**Workaround / next step:** add `list_templates` returning a per-template
manifest of {module → behavior overrides}. Alternatively make
`get_block_schema(module, templateId)` template-aware.

---

### Test 4 — Login method knowledge & configuration

**Prompt (verbatim):**
> What login method should i use for my website? what are the differences
> between all of them? configure the most appropriate login method for me.

**Goal:** recommend a login type, explain trade-offs, then mutate the site's
auth config.

**MCP tools used:** `get_site`, `get_block_schema` (`fast-login`),
`list_block_modules`.

**Steps & results:**
1. `get_site` shows site-level `auth.type: "user-id"` with a `loginId`.
2. `list_block_modules` includes a `fast-login` block but the schema gives no
   list of supported providers (Xsolla Login, social, custom JWT, etc.) and
   no comparison data.
3. There is **no** `update_site` / `update_auth` tool. Even if the agent picked
   the "right" method, it cannot apply it.

**Outcome:** ⚠️ partial — added a login *block* to the page, but couldn't
change the site's auth method.

**What I actually did:** `create_block_via_api` with `module: "fast-login"`,
`version: 1`. Returned `blockId: 6a15d60e397bda3c0dedce55`. This places the
existing site-level auth (user-id) on the page; it does not select a new
login method.

**What I couldn't reach:**
- No auth-method catalogue: schema gives no enum of supported providers and
  no trade-off metadata.
- No `update_site` / `update_auth` — site-level `auth.type` can't be changed
  through the MCP.

**Workaround / next step:** add `list_login_methods` (with trade-off blurbs)
and `update_site_auth(merchantId, projectId, domain, authConfig)`.

---

### Test 5 — Custom "Welcome back, hero" block (SB SDK auth)

**Prompt (verbatim):**
> Create a custom "Welcome back, hero" block that shows a personalized greeting
> with the user's avatar and a "claim daily reward" CTA. Use SB SDK auth to
> detect login state. Style it like a fantasy RPG UI - parchment background,
> glowing borders, animated rune ornaments.

**Goal:** AI-generated React block wired to SB SDK auth.

**MCP tools used:** `create_ai_block` (failed), `create_block_via_api`
(`sb-daily-reward`, succeeded).

**Steps & results:**
1. Attempted `create_ai_block` with a full Welcome-back-hero JSX (parchment
   gradient, rune animation, mocked auth). **`create_ai_block` returned a
   non-JSON HTML response — failed before my code was even evaluated.** Retried
   with a one-line minimal `MinimalTest` component; same HTML error. **The AI
   block tool itself is broken on this server right now**, independent of any
   code I send.
2. As the closest native equivalent for "claim daily reward CTA", created the
   `sb-daily-reward` federated block →
   `blockId: 6a15d618a06c5113f8f23d8c`.
3. Even if `create_ai_block` were healthy, the import allowlist (`react` +
   `@site-builder/block-utils`) exposes only `useInternalBlockSelector` /
   `useInternalChangeBlock` — no `useUser` / `useAuth` / `useRewards`. The
   "use SB SDK auth to detect login state" part of the prompt has no surface.

**Outcome:** ❌ blocked (two independent issues — broken `create_ai_block`
endpoint, **and** missing SB SDK auth hooks).

**Workarounds / next step:**
- Fix the `create_ai_block` endpoint to return JSON (currently returns an
  HTML error page that crashes the MCP client).
- Expand `@site-builder/block-utils` (or expose a sibling package) with
  `useUser`, `useAuth`, `useRewards`, etc. and document them in the
  `create_ai_block` tool description.

---

### Test 6 — Limited-time bundle (Cart + Store API)

**Prompt (verbatim):**
> Build a custom "Limited-time bundle" block. It should: pull a specific bundle
> SKU via Store API, show a countdown timer, add to cart via Cart API on click,
> animate a particle burst when added. Cyberpunk neon aesthetic - magenta/cyan,
> glitch effects, scanlines.

**Goal:** AI block calling Xsolla Store API for a bundle and Cart API on
add-to-cart.

**MCP tools used:** `create_block_via_api` (`sb-offer-chain`).

**Steps & results:**
1. Couldn't try a custom AI block — `create_ai_block` is broken (see Test 5).
2. As the closest native equivalent, created the `sb-offer-chain` federated
   block (Offer chain, supports time-windowed bundle offers) →
   `blockId: 6a15d620a06c5113f8f23e41`.
3. None of the cosmetic / behavioral specifics — countdown styling, glitch
   effects, particle burst on add-to-cart — are configurable through the
   federated block schema.

**Outcome:** ⚠️ partial — block created, no custom code, no API wiring.

**What I couldn't reach:**
- `create_ai_block` is currently broken (HTML response).
- Even if it worked, no Store/Cart API hooks in `@site-builder/block-utils`;
  no documented way to read merchantId/projectId inside an AI block at
  runtime.

**Workaround / next step:** add `useStoreItem(sku)`, `useAddToCart()` (and
similar) to the block-utils surface; fix `create_ai_block` endpoint.

---

### Test 7 — Faction selector (Store Groups + Image API)

**Prompt (verbatim):**
> Make a "Faction selector" custom block. Three tiles, each representing an
> in-game faction, pulled from Store Groups API. Hovering a tile filters items
> shown in the next Store block on the page. Use Image API for tile artwork.
> Style: dark medieval, gold trim, hover glow, smooth transitions.

**Goal:** AI block that talks to Store Groups + Image API and **cross-block
communicates** to a sibling Store block.

**MCP tools used:** `create_ai_block` schema review, `get_block_schema`
(`newStore`).

**Steps & results:**
1. No Store Groups / Image API hook in `@site-builder/block-utils`.
2. No documented inter-block messaging surface — the AI block API only
   selects/changes *its own* block state. There's no `usePageBus` or
   `setBlockValues(otherBlockId, …)`.
3. `newStore`'s `section.item.group` does accept a group ID (verified on the
   existing block — `"boosters"`), so a Store block *could* be retargeted at
   runtime in theory, but only via an inter-block channel the MCP doesn't
   expose.

**Outcome:** ❌ blocked.

**What I tried:** couldn't run a custom block — `create_ai_block` is broken
(see Test 5). No native or federated block matches "three tiles that filter a
sibling Store block", so nothing else was created.

**What I couldn't reach:** no Store-Groups / Image API hooks; no inter-block
communication primitive in the AI block runtime; `create_ai_block` endpoint
itself unreachable.

**Workaround / next step:** add `useStoreGroups()`, `useImageAsset()`, and a
documented inter-block messaging hook (e.g. `usePageState(key)`); fix
`create_ai_block` endpoint.

---

### Test 8 — Install-as-app block (PWA + Page Link API)

**Prompt (verbatim):**
> Build an "Install our store as an app" custom block that uses PWA API to
> trigger install, and Page Link API to deep-link into a specific bundle page
> after install. Mobile gaming aesthetic - chunky buttons, soft shadows, bouncy
> micro-animations.

**Goal:** AI block hooking the PWA install prompt and the Page Link API.

**MCP tools used:** `get_site`, `create_ai_block` schema review.

**Steps & results:**
1. `get_site` confirms PWA is enabled at site level (`pwa.enable: true`).
2. No `usePwaInstall()` / `usePageLink()` hook in `@site-builder/block-utils`.
   We could in theory listen for `beforeinstallprompt` on `window` from inside
   the component, but the prompt says "use PWA API" which implies a first-class
   hook — and there's no Page Link API surface at all.

**Outcome:** ❌ blocked.

**What I tried:** nothing to actually create — `create_ai_block` is broken
(see Test 5), and there is no native/federated "install-as-app" block.

**What I couldn't reach:** no PWA / Page Link hooks exposed to AI blocks;
`create_ai_block` endpoint itself unreachable.

**Workaround / next step:** add `usePwaInstall()` and `usePageLink(path)`
helpers and document them; fix `create_ai_block`.

---

### Test 9 — Style override on native Store block

**Prompt (verbatim):**
> On my Web Shop site, restyle the product cards in the native Store block:
> gradient borders that animate on hover, custom price tag shape (not a pill),
> and a "rarity" colored glow based on item type. Don't rebuild the block -
> keep it native.

**Goal:** apply deep CSS overrides to the native Store block without forking
it.

**MCP tools used:** `get_block_schema` (`newStore`), `get_block`,
`update_block` schema review.

**Steps & results:**
1. `newStore` schema exposes structural fields (alignment, tabs, login button,
   sections) and the `card.layouts.*` map seen in payloads — but **no** CSS
   override field (no `customCss`, `styleOverrides`, `tokens`, `cardCss`).
2. `update_block` patches values, but the schema constrains what keys it
   accepts. There is no escape hatch for arbitrary styles.
3. The only "raw CSS" mechanism in MCP is the `html` (Custom code) block —
   which means **rebuilding** the block, exactly what the prompt forbids.

**Outcome:** ❌ blocked.

**If blocked — what blocked it:** native Store block has no styling-extension
field.

**Workaround / next step:** add a `styleOverrides` / CSS-variables field to
the newStore schema (cardBorder, priceTagShape, rarityGlow tokens) and surface
it through `update_block`.

---

### Test 10 — Theme-level vs block-level button styling

**Prompt (verbatim):**
> I want every button across the entire site to have a yellow gradient and a
> slight tilt animation on hover. What's the right way to do this on Shop
> Builder, and apply it.

**Goal:** apply a site-wide button style (theme-level, not per block).

**MCP tools used:** `get_site`.

**Steps & results:**
1. `get_site` shows `theme.buttons[]`, `theme.buttonBorderRadius`,
   `theme.buttonTextColor`, `theme.accentColor` — exactly the fields a
   theme-level button restyle would touch.
2. There is **no** `update_site` / `update_theme` tool. None of the available
   MCP tools mutate `site.theme.*`.
3. The closest available tool — `update_block` — only acts on a single block,
   which is the wrong scope.

**Outcome:** ❌ blocked.

**If blocked — what blocked it:** missing `update_site` (or `update_theme`).

**Workaround / next step:** add `update_site_theme(merchantId, projectId,
domain, themePatch)` with a `buttons` patch that supports gradients +
hover-transform tokens.

---

### Test 11 — New feature toggles on existing Store block

**Prompt (verbatim):**
> In my Store block, add the "filters" bar and the "sort dropdown", and the
> "search" input. Also change the items-per-row from default to 4.

**Goal:** flip 3 feature toggles on `newStore` and set `itemsPerRow = 4`.

**MCP tools used:** `get_block_schema` (`newStore`), `get_block`.

**Steps & results:**
1. `get_block_schema newStore` lists these `values.*` fields: `alignment`,
   `description.enable`, `tabs` (`enable`, `type`), `loginButton`. That's it.
2. `get_block` on a real Store block reveals additional runtime keys
   (`background`, `script`, `card.layouts.*`) — but still **no** `filters`,
   `sortDropdown`, `search`, `itemsPerRow` keys.
3. Actually called `update_block` on the Store block from Test 1
   (`6a15d5b9a06c5113f8f23c7a`) with `values: { filters: {enable:true},
   sortDropdown: {enable:true}, search: {enable:true}, itemsPerRow: 4 }`.
   The call returned `updated: true` and **persisted the unknown fields to
   the block document** — `get_block` shows them written, even though the
   schema declares `additionalProperties: false`. The renderer ignores them
   (no such features exist on the block), so the prompt's visible effect is
   nil, **but the block payload is now polluted with phantom config**.

**Outcome:** ❌ blocked at the rendering level — plus a separate
schema-enforcement bug.

**Bugs surfaced:**
- The requested feature fields don't exist on the `newStore` schema (the
  original blocker).
- `update_block` does **not** validate against the schema's
  `additionalProperties: false`, so any junk keys round-trip into the DB.

**Workaround / next step:** verify on the Site Builder backend whether
filters/sort/search/itemsPerRow features exist at all; if yes, surface them
in the `newStore` schema. Independently, fix `update_block` to reject keys
not declared in `get_block_schema`.

---

### Test 12 — Multi-block reorder + Lead video bg + Store group filter

**Prompt (verbatim):**
> On my homepage: reorder blocks so Lead block is first, then a custom promo
> block, then Store, then Footer. In the Lead, set the background to a video
> URL I'll provide. In the Store, only show items from the "Skins" store group.

**Goal:** three sub-tasks — reorder, set Lead bg to video, filter Store to a
group.

**MCP tools used:** `list_blocks`, `get_block_schema` (`lead`, `newStore`),
`get_block`, `get_site`.

**Steps & results:**
1. **Reorder:** there is no `move_block` / `reorder_blocks` / `update_page`
   tool. `create_block_via_api` accepts a `position` index, so a workaround
   would be *delete-and-recreate* each block in the desired order — but that
   destroys block IDs, history, and any inbound references. Not viable as a
   real workflow.
2. **Lead video background:** `get_block_schema lead` exposes `values.logo`
   (with `type: "image"|"video"`) but no `background` field. The page/site
   theme has `videoBackground` (`get_site.theme.videoBackground.enable/video`)
   — that's where a "page background video" lives — but there is no
   `update_site` / `update_page` tool to set it.
3. **Store filter to "Skins" group:** actually executed.
   `update_block` on `6a15d5b9a06c5113f8f23c7a` with
   `components: [{ section: { item: { type: "VIRTUAL_GOOD", group: "skins" },
   title: "Skins" } }]` returned `updated: true`. (Note: `"skins"` is a
   placeholder group ID — the real Skins group ID in Publisher Account must
   replace it before this is functional.)

**Outcome:** ⚠️ partial (1 of 3 sub-tasks possible).

**If blocked — what blocked it:** missing `move_block` and
`update_page`/`update_site` (for page/site-level video bg).

**Workaround / next step:** add `move_block(blockId, newIndex)` and
`update_page_theme` / `update_site_theme`.

---

### Test 13 — Publish with custom domain + country whitelist

**Prompt (verbatim):**
> Publish my site with the custom domain shop.mygame12312313.com. And apply
> whitelist for USA and Malaysia only.

**Goal:** flip site to published with a custom domain and a country whitelist.

**MCP tools used:** `get_site`.

**Steps & results:**
1. `get_site` returns `externalDomains: []`, `restrictions: null`. These are
   the fields a publish+domain+whitelist operation would set.
2. There is **no** `publish_site` / `unpublish_site` / `add_custom_domain` /
   `set_restrictions` tool in the MCP.

**Outcome:** ❌ blocked.

**If blocked — what blocked it:** missing publish-pipeline tools entirely.

**Workaround / next step:** add `publish_site`, `add_custom_domain`, and
`set_site_restrictions(allowedCountries[])`.

---

### Test 14 — GA4 integration + custom "Cart-hit" event

**Prompt (verbatim):**
> Connect Google Analytics 4 (measurement ID G-XXXXXXX) to my site. Then add a
> custom event "Cart-hit" that fires when a user adds anything to cart.

**Goal:** set GA4 measurement ID on the site, then register a custom event
hook.

**MCP tools used:** `get_site`.

**Steps & results:**
1. `get_site.apps` has slots for `googleAnalytics`, `gtm`, `facebookPixel`,
   `twitterPixel`, `appsFlyer`, `adjust`, `singular`, `googleShopping` — but
   no MCP tool updates `apps.*`.
2. The "make your own cake" mechanism the prompt references (Xsolla's
   custom-event UI) has no MCP surface either — there's no
   `register_custom_event`, no `attach_event(blockId, event)`.

**Outcome:** ❌ blocked.

**If blocked — what blocked it:** missing `update_site_apps` /
`set_analytics` and missing custom-event API.

**Workaround / next step:** add `set_analytics(provider, id)` and
`add_custom_event(name, trigger)`.

---

### Test 15 — Unpublish + rollback to previous version

**Prompt (verbatim):**
> Unpublish my site immediately - we have a critical issue. Then roll back to
> the previous published version and republish that one.

**Goal:** emergency unpublish, version restore, republish.

**MCP tools used:** `get_site`.

**Steps & results:**
1. `get_site.version` returns a numeric version (22 for our site) — so the
   server tracks versions. But the MCP exposes neither a
   `list_site_versions` / `get_site_version` read tool nor a
   `restore_site_version` / `unpublish_site` / `republish_site` write tool.

**Outcome:** ❌ blocked.

**If blocked — what blocked it:** no version-management or publish-state tools
at all.

**Workaround / next step:** add `unpublish_site`, `list_site_versions`,
`restore_site_version(versionNumber)`, and (re)`publish_site`.

---

## Summary

| #  | Test                                       | Outcome     | Block ID(s) created on Hamster Tap Tap          |
|---:|--------------------------------------------|-------------|-------------------------------------------------|
| #  | Test                                       | Outcome     | Block ID(s) — mcp-test run                       |
|---:|--------------------------------------------|-------------|--------------------------------------------------|
| 1  | Web Shop + Store for game keys             | ⚠️ partial  | `6a15dd0e5de2b1d331c01443` (newStore, UNIT, game-keys-vertical layout — only after manually supplying card) |
| 2  | List blocks with restrictions              | ⚠️ partial  | — (read-only)                                    |
| 3  | Cross-template behavior                    | ❌ blocked  | — (read-only)                                    |
| 4  | Login method knowledge & config            | ⚠️ partial  | `6a15dd55049c9d36b2255c3a` (fast-login; site auth unchanged) |
| 5  | "Welcome back, hero" (SB SDK auth)         | ❌ blocked  | `6a15dd77049c9d36b2255c51` (sb-daily-reward as closest proxy; create_ai_block broken) |
| 6  | Limited-time bundle (Cart + Store API)     | ⚠️ partial  | `6a15ddb5049c9d36b2255caf` (sb-offer-chain as closest proxy) |
| 7  | Faction selector (Store Groups + Image)    | ⚠️ partial  | `6a15ddcd049c9d36b2255cde` (bento-grid as closest proxy — 3-tile layout supported, no Store-Groups wiring) |
| 8  | Install-as-app (PWA + Page Link)           | ❌ blocked  | — (no matching block; AI block broken)           |
| 9  | Style override on native Store block       | ❌ blocked  | —                                                |
| 10 | Theme-level button styling                 | ❌ blocked  | —                                                |
| 11 | New features on Store block                | ❌ blocked* | (Store block payload polluted on prior run — see bug below) |
| 12 | Multi-block reorder + bg + group filter    | ⚠️ partial  | `6a15ddd6049c9d36b2255cf5` (lead block created; no bg field, no reorder tool; group filter doable via update_block components) |
| 13 | Publish + custom domain + whitelist        | ❌ blocked  | —                                                |
| 14 | GA4 + custom event                         | ❌ blocked  | —                                                |
| 15 | Unpublish + rollback                       | ❌ blocked  | —                                                |

Extra block created on `mcp-test` for completeness:
`6a15dde8a06c5113f8f24c8b` — `hero` (Call-to-action) — defaults only.

*= no visible effect, but write succeeded with silent schema violation; see Test 11 bug.

Top recurring gaps, in order of how many tests they break:

1. **No `update_site` / `update_site_theme` / `update_site_apps`** — breaks
   tests 4, 10, 12, 13, 14.
2. **No publish pipeline (`publish_site`, custom domain, restrictions,
   versions)** — breaks tests 13, 15.
3. **AI block runtime is missing first-class hooks for SB SDK** (auth, store,
   cart, store-groups, image, PWA, page-link, inter-block messaging) — breaks
   tests 5, 6, 7, 8.
4. **No template-awareness** in `get_site` / `get_block_schema` /
   `list_block_modules` — breaks tests 1, 2, 3.
5. **`get_block_schema` under-reports real fields** (e.g. `card.layouts`,
   game-keys options on newStore) — breaks test 1, contributes to 9 and 11.
6. **No `move_block` for reorder** — breaks test 12 (reorder sub-task).

New bugs surfaced during real-create runs:

- **`create_ai_block` endpoint returns HTML, not JSON.** Reproduces with a
  one-line minimal component. MCP client surfaces it as
  `Unexpected token '<', "<!DOCTYPE "... is not valid JSON`. This makes
  *all* custom-block prompts unrunnable, regardless of code or auth.
- **`update_block` does not enforce schema `additionalProperties: false`.**
  Sending unknown `values.*` keys returns `updated: true` and persists them
  to MongoDB. The renderer ignores them, so the prompt has no visible
  effect — but the block document accumulates phantom config (verified on
  `6a15d5b9a06c5113f8f23c7a` before it was deleted).
- **`create_block_via_api newStore` doesn't apply section `card` defaults.**
  A `NEW_STORE_SECTION` created via API without a `card` field is persisted
  partial; the editor then crashes with `Cannot read properties of undefined
  (reading 'selectedLayoutType')`. The server should either inject a default
  `card` or reject the request — currently it does neither.
- **No `create_page` tool.** The MCP can read pages (`get_page`,
  `list_pages`) and create blocks *on* an existing page, but cannot create a
  new page on a site. Same gap for `delete_page` and `update_page_meta`. Any
  flow that begins "make a new empty page and add X" has to start in the
  Publisher UI to get a `pageId`, then hand that ID to the MCP.
