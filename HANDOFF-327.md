# Build 327 handoff

For a fresh session picking this up. Build 327 is branch `wip/build-327`, which is build 326 (`wip/build-326`, 5ce026a) plus five packages: A sound, B the XP box and hundo effects, C the story, recap and calendar, D glass, units, tab bar, lobby, stars and Save and exit, and E stats, history, the badge case and the crack. The notes for each package are at the end of CLAUDE.md, under "Build 327".

## State
- NOTHING IS LIVE. `main` is still the build before 326. Do not merge or push to `main` until Madison says go.
- `APP_BUILD` and `version.json` are still `2026-10-18-326` on this branch. The bump was refused as a deploy-shaped action during integration. It is part of the go: bump both to the same value (e.g. `2026-10-2x-327`) in one commit.
- The sound videos (10 clips, recorded with `tools/record-sound.py`) were sent to Madison in the chat. They are not in the repo.

## On Madison's go, in this order
1. Bump `APP_BUILD` and `version.json` `build` together.
2. Do the 326 handoff steps: set `studyLogCaps().leakUntil` to the ship date, and set the `at` date on the `NOVA_BROADCASTS` v9-dms entry.
3. Merge `wip/build-327` into `main` and confirm it is live (Pages rebuilds in about a minute).

## Gates on the merged build (Oct 20)
- Pass: check-js, check-b327-a/b/c/d/e, check-sound, check-sync, check-friends, check-unlocks, check-curve, check-tours, check-statsbadges, check-profilecard, check-save-code, check-readd, check-savetest, check-studyflow, check-study-time, check-trend, check-chat, check-chatroom, check-groupchat, check-loops, check-edges, check-b326-a through g, check-vroom, check-positions, and sweep-layout (74/74 clean).
- Fail on 326 identically, so not caused by this build:
  - check-results: iPad heading gap [23.8, 19.8].
  - check-fixes: iPhone SE 1st gen 568x260 GREY BAR.
  - check-behaviour b313_fx: Underwater and UFO "tail never cut" (`rs-pct-sign`).
- check-behaviour b323b_stars "status-bar band untouched" (233): fails on 326 identically.
- check-behaviour b318_planet (Supernova rings, ten fast taps): with SOUND ON each tap's sound makes frames uneven enough to read 1.35x against 1.2x per frame. Build 326 with sound switched on reads the same, so the section now measures with sound off. Worth Madison spamming the Supernova planet on her phone to feel whether the taps hitch.
- Flaky under load, passing alone: check-b326-e (Nova's scheduler), and check-behaviour b313_notice "se: the planet goes back".
- check-behaviour runs in chunks via `ONLY_FN` (the whole run is over 2 hours). Three Penal Code sections now pin the page clock before `PENAL_256_AT` (`PIN_BEFORE_PENAL_256`), because the app switched to slides 256-578 on Oct 19.

## Decisions Madison has not answered (each is built one way)
1. **Weekly recap:** it ends "That's the week. See you all next Tuesday." after the class totals. Cut that line if "that's it" means stop dead on the numbers.
2. **Cracks cannot be avoided in the app:** every rank from Gold adds one and nothing repairs them. The story now treats cracks as strain and badges as what holds the planet together. Making cracks avoidable would change how the app works.
3. **"Smaller ash mark"** was read as the crazing on the planet's highlight, which is removed. `SCAR_SHINE_CRAZE = true` brings it back.
4. **Test history's average ring** is coloured by result (green, gold or red). The alternative is grey, like Stats' accuracy ring.
5. **"Hundos ×2"** keeps the ×N even with the units listed under it.
6. **A climb that stops at the next rank's wall** switches from "N extra XP" to the wall's usual "x / y XP".
7. **The calendar still has the same number of boxes.** The next step, if it still feels busy, is to fold "This week" into Today.
8. **Sound is on for everyone once**, recorded on the account (`theme.soundOn327`) and on the device. It is untested on a real iPhone, since there is no WebKit here.
9. **Glass, stars, the badge case and the crack** were judged in Chromium, which does not draw backdrop blur faithfully. They need a look on her phone.

## Carried from 326, still open
- The crew slide still reads "5 of 30 characters found". She has not said whether she wants it changed.
- About two frames of empty stage between the badge slide and the crew slide in Nova's introduction. This may be a recording artifact.
- A dark secret flare can sit partly behind a big rank flare on Home.
