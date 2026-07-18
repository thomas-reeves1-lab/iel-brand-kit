# WIRING - iel-brand-kit

Last verified: 18 Jul 2026

## What this is

The IEL brand asset store: logo, 47 icons, banners, favicons, letterhead, brand board. It is a
**public** GitHub repo with no build step and no code on `main` - consumers hotlink the raw
GitHub URLs straight into the Mission Control app, welcome emails and Notion pages.

## Entry points

There is no runnable entry point on `main`. The repo is served, not executed.

| What | How |
|---|---|
| Add or replace an asset | Drop the PNG in the right folder, add the row to `brand_urls.json` AND `URL_MAP.md`, commit, push to `main`. Live on the raw URL within seconds. |
| Look up an asset URL | `URL_MAP.md` (human) or `brand_urls.json` (machine-shaped, see below) |
| Check the map is honest | `python scripts/validate_brand_urls.py` - **only on branch `ci/verify-gate` / PR #1, not yet on `main`** |

## Data flow

```
Design/build scripts (iel-invoicing-engine)   LOCAL, MANUAL
  scripts/build_brand_kit.py, build_icon_set*.py, build_brand_assets.py,
  build_policies_header.py
    -> iel-invoicing-engine/docs/superpowers/deliverables/**
    -> [HAND COPY - no script does this] -> iel-brand-kit/<folder>/
    -> git push main
    -> https://raw.githubusercontent.com/thomas-reeves1-lab/iel-brand-kit/main/<path>   LIVE, PUBLIC
         |
         +-> Mission Control app  LIVE  (src/02_icons.js: BASE + LOGO_URL + FAVICON_URL, hardcoded)
         +-> Welcome / exit emails  LIVE  (ONB_LOGO_URL cell on the IEL MC Config sheet)
         +-> Notion pages  LIVE  (page icon URLs pasted into Notion itself)
         +-> iel-daily-brief  LOCAL  (reads C:\iel\iel-brand-kit\Banners\IEL_Icon_Square.png off disk)
```

## Folder layout

| Folder | Holds |
|---|---|
| `Icons/` | 47 topic icons, `iel_<name>.png`, 256x256 transparent |
| `Brand/` | brand board, pattern, circular avatar, A4 letterhead, email signature |
| `Banners/` | Notion cover header, brand strips (`IEL_Brand_Strip.png`, `Strip1`, `Strip2`), square app icon |
| `Favicons/` | favicon.ico + PNG sizes 16-512, apple-touch-icon, leaf mark, wordmark, `manifest.webmanifest` |
| `Logo/` | `iel_logo_navy.png` - the welcome-email logo |
| `Previews/` | icon contact sheets, reference only |

## brand_urls.json and URL_MAP.md

`brand_urls.json` has three keys:

- `base` - `https://raw.githubusercontent.com/thomas-reeves1-lab/iel-brand-kit/main/`
- `files` - 75 entries, keyed by repo-relative path (`Icons/iel_risk.png`), value is the full raw URL
- `by_name` - 61 entries, keyed by bare stem (`iel_risk`), same URLs. **Favicons are not in `by_name`.**

`URL_MAP.md` is the same 75 rows as a markdown table for humans. Both are hand-maintained.

**No code in the estate reads `brand_urls.json` at runtime.** Every consumer hardcodes its URLs.
The JSON is a published index and a drift check, not a live interface. Nothing generates it either -
it is edited by hand.

## Credentials

None. No tokens, no secrets, no `.env`. The repo is public and read access needs nothing. Pushing
uses the machine's normal GitHub auth (`gh` CLI / git credential manager). Nothing here is in
Bitwarden because nothing here is a secret. Do not put anything in this repo that should not be
world-readable - it is a public CDN.

## External services

| Service | What for | Notes |
|---|---|---|
| raw.githubusercontent.com | serves every asset | Public, anonymous. GitHub caches raw responses ~5 min, so a replaced file can look stale briefly. No API key, no rate limit that matters at this volume. |
| GitHub Actions | the verify gate | Only on PR #1 branch. Runs on PR and push to `main`. |

## State and caches

The repo holds no state files, counters or caches. Every file is a source asset or a hand-written
map. Nothing here is safe to "regenerate" automatically - the build scripts in `iel-invoicing-engine`
write to that repo's `deliverables/` folder, **not** into this one, so re-running them does not
refresh these files.

## Scheduled / automated

Nothing scheduled fires against this repo. No cron, no watcher, no auto-commit found in the estate.
The only automation is the CI verify job that PR #1 adds.

## Gotchas

1. **The repo is PUBLIC and hotlinked. A rename or delete breaks images everywhere at once, silently.**
   No consumer holds a copy. Rename `Icons/iel_risk.png` and every Notion page using it shows a broken
   image, with no error anywhere. Assets are append-only in practice - add the new one, leave the old
   one in place.
2. **Renaming the repo itself breaks every Notion image.** The repo name is inside every raw URL.
   `C:\iel\iel-setup\docs\00-session-context.md` and `C:\iel\iel-mission-control\docs\new-pc\02-repo-plan.md`
   both say the same thing: never rename `iel-brand-kit`.
3. **`brand_urls.json` and `URL_MAP.md` must be updated by hand with every asset change.** They already
   drifted: `Banners/IEL_Brand_Strip1.png` and `Banners/IEL_Brand_Strip2.png` (added 10 Jul 2026) are on
   disk and on the public URL but appear in neither map.
4. **The verify gate only checks one direction.** `scripts/validate_brand_urls.py` (PR #1) walks the map
   and fails if a listed file is missing on disk or its URL does not equal `base + path`. It does **not**
   flag a file on disk that is absent from the map - so gotcha 3 passes the gate.
5. **The gate is not on `main` yet.** It lives on branch `ci/verify-gate` (PR #1, open). Until that
   merges, nothing stops a bad push.
6. **`Favicons/` is missing from `by_name`.** Anything looking up by bare stem will not find a favicon.
   Use the `files` map or the full path.
7. **README.txt is misleading about regeneration.** It says assets re-generate from
   `iel-invoicing-engine/scripts/build_*.py`. Those scripts exist, but they output to
   `iel-invoicing-engine/docs/superpowers/deliverables/`. The copy into this repo is manual and
   unscripted, and nothing detects drift between the two locations.
8. **The welcome-email logo is a spreadsheet cell, not code.** `ONB_LOGO_URL` on the IEL MC Config
   sheet points at `Logo/iel_logo_navy.png`. It is consumed by
   `C:\iel\iel-mission-control\src\11_onboarding.js` (welcome) and `src\12_lifecycle.js` (exit), and
   guarded by `WELCOME_KEYS` in `src\14_selfcheck.js`. No test checks the URL resolves - a typo or a
   renamed logo means every welcome email ships a broken image.
9. **Mission Control's icon list is hand-maintained.** `C:\iel\iel-mission-control\src\02_icons.js`
   holds `BASE` (line 17), `LOGO_URL` (24), `FAVICON_URL` (29) and a `MAP` of icon keys.
   `tests\run.js` pins those three literal strings but verifies nothing about the remote files.
10. **One consumer reads this repo off disk, not by URL.**
    `C:\iel\iel-daily-brief\scripts\make_icon.py:14` hardcodes
    `C:\iel\iel-brand-kit\Banners\IEL_Icon_Square.png`. It breaks on any machine where this repo is not
    cloned to that exact path - the integrity-officer PC deliberately does not clone it.

## Verify

```bash
# 1. Map matches disk (once PR #1 is merged; until then run it from that branch)
python scripts/validate_brand_urls.py
# expect: OK: brand_urls.json is consistent (136 entries checked).

# 2. Every tracked file is in the map (catches the gap the gate misses)
python -c "import json,subprocess;m=set(json.load(open('brand_urls.json'))['files']);t=set(subprocess.check_output(['git','ls-files'],text=True).split());print(sorted(t-m-{'brand_urls.json','URL_MAP.md','WIRING.md'}))"
# expect today: ['Banners/IEL_Brand_Strip1.png', 'Banners/IEL_Brand_Strip2.png']  (known drift, gotcha 3)

# 3. The public hotlink actually serves
curl -s -o /dev/null -w "%{http_code}\n" -I https://raw.githubusercontent.com/thomas-reeves1-lab/iel-brand-kit/main/Logo/iel_logo_navy.png
# expect: 200

# 4. Repo is still public and still named iel-brand-kit
gh repo view --json name,visibility
# expect: {"name":"iel-brand-kit","visibility":"PUBLIC"}
```
