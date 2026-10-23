# b327z5-b - sheets you can pull down from anywhere, a close X you can see

Madison: *"The chat box when it's up, you can't swipe down from it unless you
are swiping down from the very top."* and *"The test start menu with all the
options. The swiping down function is broken. It doesn't swipe down similar to
how the chat one doesn't. The x button in the top right you can't see it cause
color. When you do swipe down it glitches and changes colors."*

Base 619542a. Gate: `tools/check-b327z5-b.py` (`B327Z5B_ONLY=A|B`,
`--against FILE`): 24 failures on 619542a, ALL PASS here. Real CDP touch on an
iPhone 17 Pro Max (440x956 at 3x) and an iPad Pro 11" (834x1194).

## The start sheet (`attachSheetSwipe`: Drill/Quiz/Review and the VR Match settings)

- **From anywhere, when the scroller under the finger is at its top.** It used
  to take the sheet on the first pixel of any move (a tap that slid moved it,
  a sideways slide pulled it) and asked only the sheet's own scrollTop. Now it
  finds the nearest vertical scroller under the finger: scrolled down, or a
  sideways first move, is a scroll; at the top, every move is claimed from the
  first (iOS will not give back a move it committed to a bounce); past
  `SHEET_SWIPE_SLOP` (12px) a down drag follows the finger 1:1 (translate3d
  written once a frame), an up drag scrolls the list by hand. Sliders, fields,
  selects are skipped.
- **No colour change.** `.is-dragging` carried its own lighter blue-grey fill,
  which out-ranked the start sheet's `#0F1115`; it now only drops the blur
  (both dragged sheets are opaque, so the blur shows nowhere).
- **Closes or springs back smoothly**: past min(110px, 22% of its height) or
  a flick, it slides all the way out at about the finger's speed (180-300ms)
  and only then closes; short of it, a .32s spring back; a generation counter
  stops a stale timeout touching a newer drag.
- **The close X is visible**: the white button recipe out-ranked the round
  icon's rules (a near-white X on a near-white disc, 1.0:1). It is a glass
  circle again (13% white lift, lit rim, white X drawn by ::before/::after):
  13.4:1 phone / 10.7:1 iPad, the 44px target unchanged.

## The chat sheet

- **Down from anywhere.** The head is unchanged (every move ours, down closes,
  up resizes). Anywhere else that is not a text field, the tablet's size
  handle or the emoji tray: a drag that goes DOWN with the list under the
  finger at its top pulls the sheet; up, sideways (the roster), or starting
  with the list scrolled is the list's, and the page guard keeps it off the
  page. Outside the head the slop is `DRAG_SLOP_BODY` (22px, a thumb's tap
  jitter), only a downward move arms, and coming back up only returns the
  sheet to rest - it never resizes. The delayed flat fill (`DRAG_FLAT_AT`)
  is unchanged, so a tap still never moves or recolours the glass.

## Gates

- check-b327z5-b: ALL PASS (24 failures on 619542a).
- check-b327-h: ALL PASS. check-chatroom: ALL PASS.
- check-chat: one failure, "the what's new card is missing one of the things
  it was asked to say, or is not Version 9" - identical on 619542a, unrelated.
- check-behaviour b314h_sheet (99), b314h_chat (98), b314h_chat2 (105), b297
  (65), b267 (49): ALL PASS.
- check-js: OK.
