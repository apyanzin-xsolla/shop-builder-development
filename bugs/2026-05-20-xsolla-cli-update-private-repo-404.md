# xsolla-cli: `xsolla update` returns GitHub 404 because the private repo requires auth and no token can be passed

- **Tool:** xsolla-cli
- **Version:** v1.8.3 (commit `08c5855`, darwin/arm64, go1.26.1)
- **Affected command:** `xsolla update` (and `xsolla update --check`)
- **Affected docs:** `README.md` "Command Reference" table — lists `xsolla update` as "Update CLI to the latest version"
- **Date observed:** 2026-05-20
- **Reporter:** a.pyanzin@xsolla.com

## Expected result

Per the README ("Command Reference" table) and `xsolla update --help`:

```
Check for and install the latest version of the Xsolla CLI.

By default, downloads the latest release from GitHub, verifies its checksum,
and replaces the current binary in-place.
```

Running `xsolla update --check` should report whether a newer release exists; `xsolla update` should download and install it.

## Actual result

```
$ xsolla update --check
Checking for updates...
checking for updates: GitHub API returned status 404
```

The `xsolla/xsolla-cli` repository is **private**, so GitHub's REST API returns 404 to anonymous callers — this is the standard private-repo behavior, not a missing release.

`xsolla update` has **no flag or env var to authenticate** the GitHub call. Confirmed by inspecting `xsolla update --help`:

```
Flags:
      --check            Only check for updates, do not install
      --version string   Install a specific version (e.g. 1.7.0)
  -y, --yes              Skip confirmation prompt
```

No `--github-token`, `--auth`, or similar. Passing `GITHUB_TOKEN` as an env var has no effect:

```
$ GITHUB_TOKEN="$(gh auth token)" xsolla update --check
Checking for updates...
checking for updates: GitHub API returned status 404
```

Debug log shows the CLI loads its own Xsolla tokens from Keychain (bearer + API key), but never authenticates the GitHub API call:

```
[DEBUG] Loaded bearer token from keychain for profile "default" (in-context, no env leak)
[DEBUG] Loaded API key from keychain for profile "default" (in-context, no env leak)
Checking for updates...
checking for updates: GitHub API returned status 404
```

**Net effect:** `xsolla update` is a no-op for every current CLI user, since the only place the CLI is distributed (this private repo) cannot be read anonymously.

## What is incorrect in the README

1. `xsolla update` is listed as a working command in the Command Reference, but in this release it is unusable due to the private-repo distribution model.
2. The README's install section already requires `GITHUB_TOKEN` for the shell-script installer, but the `update` command doesn't consume that same token.
3. The error message (`GitHub API returned status 404`) is misleading — it doesn't say "auth required for private repo" or suggest a workaround.

## Repro steps

1. Install xsolla-cli v1.8.3 (any install method)
2. `xsolla update --check` → `GitHub API returned status 404`
3. Set `GITHUB_TOKEN` to a valid PAT with `repo` scope and SAML-authorized for `xsolla` org
4. `GITHUB_TOKEN="<token>" xsolla update --check` → same 404 (env var is ignored)
5. No flag accepts a token: `xsolla update --help` confirms only `--check`, `--version`, `--yes`

## Suggested fix

Pick one:

1. **Consume `GITHUB_TOKEN`** — the CLI should send the env var as a Bearer header when calling `api.github.com/repos/.../releases/latest`. Document it in `update --help`. Smallest, most consistent change — already aligns with the install-script behavior.
2. **Reuse the CLI's own GitHub authentication** — e.g. require `gh auth login` and read the token via `gh auth token`, or store a release-feed token in Keychain like the Xsolla JWT.
3. **Distribute releases over an authenticated Xsolla endpoint** instead of GitHub, so users don't need a GitHub PAT at all.
4. **At minimum, improve the error message** to mention the private-repo case and point users to the manual `gh release download` workaround until the above is fixed.

## Related bugs in this folder

- [`2026-05-20-xsolla-cli-publisher-status-not-configured.md`](./2026-05-20-xsolla-cli-publisher-status-not-configured.md) — `publisher status` / `list-projects` / `list-api-keys` / `create-project` false negative
- [`2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md`](./2026-05-20-xsolla-cli-readme-shopbuilder-session-cookie-outdated.md) — README points to non-existent `ps2[user_session]` cookie
- [`2026-05-20-xsolla-cli-readme-missing-create-website-command.md`](./2026-05-20-xsolla-cli-readme-missing-create-website-command.md) — `webshop create-website` / `update-website-theme` commands missing
