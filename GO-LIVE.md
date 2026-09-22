# This repo is live

`https://chyjyrkwn7-eng.github.io/index.html/` is the link Class 26E
uses. The repo is *named* `index.html` — that is the repository name,
not a path — and the Pages URL follows from it.

**A merge to `main` is a deploy to ~40 people, live in about a minute.**
There is no staging copy to try it on first: the `Nova-Test` repo this
was built in has been retired. Run the gates in `CLAUDE.md`
(**Verifying**) before merging, not after.

## What has to stay together

| File | Why |
|---|---|
| `index.html` | the app |
| `version.json` | the other half of the update check — its `build` must equal `APP_BUILD` inside `index.html` |
| `launch/` | 42 iOS startup images, referenced **by path** from `index.html` |

Those three are one unit.

- Bump only `version.json` → everyone gets a banner reloading can never
  clear.
- Bump only `APP_BUILD` → nobody is ever told there is an update.
- Lose `launch/` → every iPhone gets a white flash on open, and nothing
  anywhere says why. iOS reads those images at launch, before the page
  loads.

`tools/` and `CLAUDE.md` are for whoever maintains this; nothing at
runtime reads them. `launch/`, by contrast, **is** read at runtime.

## The re-add prompt has been spent

`frameId` is `go-live-1`. It fired once, on build 97, when the icon, the
app name, the status bar colour and the launch images all arrived at
this origin for the first time — everything iOS reads only at install.

**Do not bump `frameId` again** unless one of those four genuinely
changes. Bumping it is the only thing that re-prompts a device that has
already acknowledged, and a prompt for nothing is a prompt people learn
to dismiss.

## Checking a deploy

1. `curl <url>/version.json` → `build` matches `APP_BUILD` in the served
   `index.html`.
2. `curl -I <url>/launch/1320x2868.png` → `200`, `image/png`. A 404 here
   means `launch/` did not publish, which is the silent white-flash
   failure.
3. Open it. The bottom tab says **Leaderboard**; Profile's fourth tab
   says **Rank**.

## History

Build 97, 2026-09-22: the app, `version.json`, `launch/`, `tools/` and
`CLAUDE.md` were copied here from `Nova-Test` and that repo was retired.
Everything in this file that used to describe *how to copy across* is
gone, because there is nowhere to copy from any more.
