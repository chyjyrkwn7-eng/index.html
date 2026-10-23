# Build 327z5 (C) - every notice on the account banner's glass, centred

Branch `b327z5-c` off 619542a. Gate: `tools/check-b327z5-c.py` (`--against`);
ALL PASS here, 35 failures on 619542a.

Madison loved the save-your-code banner (neutral glass, a 3px coloured bar on
the left, a bare icon, a small tag, one sentence, an x). Everything below is
on that recipe; no banner carries a wash of its colour ("Why is there yellow
in it like that?").

- **Welcome back is a top banner, not a toast** (`showWelcomeBackBanner(msg)`,
  `#welcome-banner`, kind `welcome`: tag WELCOME BACK, green, a cloud with a
  tick). Every `showToast("Welcome back...")`, "Signed back in", "Signed in to
  your account" and "Linked - this device is now synced." call goes through it.
- **Save and exit lands on Home with a SAVED TEST banner**
  (`showSavedTestBanner()`, `#savedtest-banner`, blue bookmark): "Your test is
  saved - tap Start Studying to pick it up." Only if Home is up 600ms later.
- **The key is drawn in strokes** (round bow, shaft, two teeth; it was one
  filled outline that blobbed at 21px). **Rank up is three climbing chevrons**
  at .4 / .7 / 1, no star. `BANNER_KINDS` takes `svg:` for any kind.
- **Every top banner is centred**: left = right = max(1rem, insets),
  max-width min(26rem, 100vw - 2rem); the phone's right-only inset (which
  cleared the chat button by stopping short of it) and the daily banner's own
  narrower rule are gone. `settleTopBanner(el)` moves a banner below the chat
  button (`.chatdock-btn`, `#roomchat-fab`) or another top banner it would
  overlap, so two banners stack instead of sitting on each other. Called from
  `positionDailyAlert(el)` and `placeTopBanner(el)`.
- **Icon, words and x on one centre line**: the x is a drawn path
  (`BANNER_X_SVG`, a `var` - read at boot) in a grid-centred box; a typed "x"
  sat on its baseline. Measured within 0.1px on both reference devices.
- **Every daily-question message is the top banner.** "It's out" was the
  bubble beside the "?" (`showDailyTip`, now unused); it is the live banner
  (`#dailyalert.app-banner.is-live`, tag DAILY QUESTION, a chevron, tappable,
  role button), still unrolling out of the "?" with motion on. No sweep, no
  coloured ring. "Done for today" was already a top banner (327z3).
- **The ring is the button's rim** (`.dq-ring` inset -1px, was -6px with the
  button's own grey rim and a dark gap between - two rings). Stroke 5.6, a
  faint track, round caps while it fills, the button's border stood down
  (`:has(.dq-ring)`), and nothing drawn at 0 (`.is-empty`, except while it
  charges - the charge animates from empty).
- **Toasts take the banners' look** without moving: a 3px bar on the left in
  their colour (blue plain, green good, amber star), a bare icon, role status.
  `.toast-flag` lost its solid yellow fill.
- Not touched: the tab bar, the chat button, cards.

Gates moved: check-statsbadges 3 ("It's out" is the centred top banner, no
bubble; measured after its unroll finishes).

Runs (one at a time): check-js OK, check-b327z5-c ALL PASS (35 fail on
619542a), check-b327z3 ALL PASS, check-statsbadges ALL PASS, check-save-code
ALL PASS, check-fixes --only "17 Pro Max" and --only "iPad Pro 11" all
verified.

Note: midway through, /opt/pw-browsers/chromium-1194 disappeared (the
browsers were reinstalled as chromium-1243 by something else on the box);
every gate above ran before that. The last ring tweak (excluding
`.is-charging` from `.is-empty`) was gated by check-b327z5-c before it went.
