# Fire Code's prestige (384.126 and 384.134, never shipped)

On `claude/b384-final` Fire Code had three prestiges (built in 384.126, commit `ff832e6`; shown in Virtual Rooms in 384.134, commit
`cafaa10`): a status you took with a button once you were Supernova and held gold rims in the unlock tracks. Each one gave a
character (Deputy Marshal `pgdeputy`, Fire Marshal `pgmarshal`, State Fire Marshal `pgstate`), a banner (Oath of Office `pgoath`,
Command Staff `pgcommand`, Marshal's Laurel `pglaurel`) and an emblem beside the name (Profile, the person card, the Leaderboard row,
a friend's profile, the rank ladder, and every Virtual Room surface). It was stored as one count, `store.prestige` (0-3), and
published as `pg` on Fire Code's board row and in a Fire Code room's entry.

Madison: "If we have any prestige stuff in the app, remove it. We don't want it. Our rank up system is solid." It never reached
`main` (main 7bdca1e, 384.107, has no `prestige` anywhere), so no live account ever held one.

## What is here

| File | What it is |
|---|---|
| `prestige.patch` | `git diff fa11d79 <removal commit> -- index.html`: every line the removal took out of the app (CSS, model, characters and their drawings, banners and their art, emblems, the Prestige screen, confirm sheet and ceremony, the board / card / profile / ladder emblems, the Virtual Room `pg`, the Customize groups) |
| `tools/check-b384-prestige.py`, `tools/b384_prestige_lib.py` | 384.126's gate and its real-shaped fixtures |
| `tools/shoot-b384-prestige.py`, `tools/record-b384-prestige.py` | its screens and the ceremony's recordings |
| `tools/check-b384-vrprestige.py`, `tools/shoot-b384-vrprestige.py` | 384.134's gate and screens |

## What the removal kept or changed

- The unlock tracks keep their layout. Their last tier was "the prestige tier" (a "P" on its chip) in the academy and "the gold tier" in
  Fire Code; it is now the gold tier in both classes (its number on the gold chip). The tier flag in `unlockTrackView` is `goldTier`
  (was `prestige`), the row class `is-gold` (was `is-prestige`).
- `applyLoadedData` deletes a `prestige` a test build left, and `writeAccount` never writes one back (account and `__floor`).
  An old `pg` on a board row or a room entry is never read.
- The `rays` backdrop type stays in `drawAvatarCharSVG` (nothing else uses it now; it costs nothing).

## Putting it back

```
git apply -R --3way retired/prestige/prestige.patch
git mv retired/prestige/tools/*.py tools/
```

Then restore the gate edits made with the removal: `tools/check-b384-profilerows2.py` (its `oldpg` position, L7, asserts that a
stored count draws nothing - go back to the `prestige` position and L6's mark), `tools/shoot-b384-profilerows2.py` and
`tools/sheet-b384-profilerows2.py` (the `prestige` rank position). The design and every decision are in `docs/notes-archive.md`
under `### 384.126 (prestige)` and `### 384.134 (vrprestige)`.
