# Build 326 handoff

For a fresh session picking this up. Written at the end of the build 326 review round.

## State
- Build 326 is this branch, `wip/build-326`, at the commit before this note (`9984b29`).
- NOTHING IS LIVE. `main` is still the build before 326. Do not merge or push to `main` until Madison says go.
- The review pack (screenshots, videos with sound, README) was sent to Madison in the chat. The files are not stored in the repo.

## On Madison's go, in this order
1. Set `studyLogCaps().leakUntil` to the actual ship date.
2. Set the `at` date on the `NOVA_BROADCASTS` v9-dms entry.
3. Merge to `main` and confirm it is live (Pages rebuilds in about a minute).
4. Do not touch `STORE_KEY` or the sync code keys, and do not edit questions (see CLAUDE.md).

## Known open issues (found while recording the pack, not fixed)
1. A badge found together with a rank-up is never named in Nova's message. With a rank-up, a badge and a crew find all waiting, his one message names the rank and the crew member only, and the badge is marked as said, so it is never mentioned later.
2. The badge-case row is gone from What's New, but the returning tip right after it still says "your badge case opens from it".
3. The crew slide still reads "5 of 30 characters found". Madison's complaint was about the recap, which is fixed; ask whether she wants this too.
4. About two frames of empty stage between the badge slide and the crew slide in Nova's introduction. May only be a recording artifact.
5. A dark secret flare can sit partly behind a big rank flare on Home as the rings turn.

## Not done
- No iPad recording of the new-account Nova story (item 12).
- The 20 "decisions that need your answer" in the pack README are all built one way; Madison has not answered them yet.

## Other facts worth knowing
- Penal Code slides 256-578 switches on by itself at 8:00 PM Central on Mon Oct 19 (`PENAL_256_AT`). If this ships later, it is simply already on.
- The videos in the pack are drawn one frame at a time, so they cannot show real-phone lag. Madison should check the Underwater drain and the badge case opening on her phone.
- Gates: all pass except the iPhone SE 1st gen landscape seam, which is identical on build 325.
