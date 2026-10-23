# Stream A (b327z5-a) - tab bar lens, first-tap lag, Safari

Base 619542a. Code commit 611e5b0.

## What changed (index.html)
- **The lens pops under the finger.** On touch-down it starts as a
  platter-sized pill at the TOUCHED tab (`lensDown`: `s0.cx = ti.c`), not at
  the lit tab's platter, and the lit tab's platter fades out under it over
  140ms. Pressing the lit tab is unchanged.
- **The lens tracks the finger 1:1.** In `lensMove`'s rAF tick the centre is
  the finger's x every frame, plus a starting offset that closes in ~70ms
  (`f.off *= exp(-dt/.07)`), so nothing jumps. Size still springs; the
  stretch follows the finger's smoothed speed. It still runs past the end
  tabs a little (`LENS.give`). Within the drag slop the lens already follows
  (>1.5px); turning the touch into a drag still needs `TAB_DRAG_SLOP`.
- **First tap no longer builds the reverb on the spot.** `sndGraph(..,
  {lazyRev:true})` from `ensure()` fills the convolver's impulse 350ms later
  (its FFT was most of the first tap's pointerup cost).
- **The Home ambience is rendered in idle time**, not in the tap that wakes
  the sound: `startAmbience` defers `ambRendered` through `later()` and
  starts it when done, if still wanted.

## Gate moved
- `check-b325-f` F5: the tap's lens now starts at Calendar (the tapped tab)
  from its first frame and never shows over Leaderboard (marked "MOVED IN
  327z5"). It failed on the old wording because the lens no longer glides
  from the lit tab - the change Madison asked for.

## Numbers (Chromium, 4x CPU, iPhone size, real touch taps)
- First-tap pointerup handler max: 166-238ms before -> 22-55ms after.
- pointerdown max 17-24 -> 15; pointermove mean 0.3-0.5 -> 0.2-0.3ms.
- Screen build after a tap (400-1100ms mount) not changed by this stream.

## Gates
check-js OK; check-b325-f ALL PASS (after the move); check-b325-j ALL PASS;
check-sound ALL PASS; check-sync ALL PASS; sweep-layout --quick 14/14.
check-b327x: 11 failures, identical on base 619542a (the round-7 bar is not
on this branch).

## Safari - not reproduced, nothing changed
No WebKit here (`playwright install webkit` failed; it also appears to have
reshuffled /opt/pw-browsers - the coordinator re-symlinked chromium-1194).
Code reading only:
- edge-tint strips are made after the splash at z-index 2 and may be
  covered by other fixed layers; their colour is the app's dark edge colour,
  so "black bars" may be the strips themselves;
- a used fixture's localStorage is ~4KB, so a storage quota is an unlikely
  cause of the logouts.
Freeze on tab clicks, not loading after returning, logging out and the bar
colour all need a real iPhone Safari to check.

## Not verifiable here
Safari issues above; how the lens feels on a real phone; the Taptic tick.
