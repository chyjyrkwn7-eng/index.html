# The police academy's unit badges as raised pins (384.121, never shipped)

On `claude/b384-badges` (head `a68976a`) the academy's 24 unit badges were redrawn as raised pins of each unit's object, with the
same recipe as the Fire Code chapter pins (a kettlebell, scales, a patrol cap, the peace officer's star, a desk globe, a patrol car,
a scroll and quill, a gavel, a law book, a passport, handcuffs, a capsule, a heart with a plaster, a home, a teddy bear, speech
bubbles, an envelope with a wax seal, a thumbprint, a radio, a field watch, a life ring, a brain, a dove, an ear with a hearing
aid). Madison: "Revert the badges for the police academy. I'm not a fan of these new ones." So on `claude/b384-badges2` the academy
draws exactly what main 384.107 draws again (the flat struck badges, the dirt stages, the case, the cards, the earned cutscene, the
badge in your hand), and nothing in this folder is read by the app or by any gate.

## What is here

| File | Was | What it is |
|---|---|---|
| `part-6-academy.js` | `tools/chapter-objects/part-6-academy.js` | the 24 `CHAPTER_OBJ[...]` entries (the art) |
| `academy-units.json` | `tools/chapter-objects/academy-units.json` | the academy's 24 unit names, the keys the merge tool accepted |
| `snaps-academy.json` | the academy's 24 entries of `tools/chapter-objects/snaps.json` | the joins traced by `snap.py` for those parts |
| `check-b384-acadpins.py` | `tools/check-b384-acadpins.py` | the pins' own gate (ids and unlock rules equal main's, no twins, case shows 24 pins) |
| `academy-pins-tools.patch` | `git diff f13649f a68976a` of four tools | the merge tool accepting academy keys; `check-b384-objbadges.py --class academy` and its struck-token perf reference; `check-b384-chapterbadges.py` (4) holding only academy units with no object; `check-behaviour.py` check_b317_badge2 waiting 180s |

## Putting them back

The quickest route is to revert the commit that took them out (the one titled "384.121 follow-up: the police academy's badges back
to main's"). Its other parts (`tools/check-b384-badges2.py`, the notes) can stay or go. By hand:

```
git mv retired/academy-pins/part-6-academy.js tools/chapter-objects/
git mv retired/academy-pins/academy-units.json tools/chapter-objects/
git mv retired/academy-pins/check-b384-acadpins.py tools/
git apply --3way retired/academy-pins/academy-pins-tools.patch
python3 - <<'E'   # the snaps back into snaps.json
import json; p = "tools/chapter-objects/snaps.json"; s = json.load(open(p)); s.update(json.load(open("retired/academy-pins/snaps-academy.json"))); json.dump(s, open(p, "w"), indent=0)
E
python3 tools/merge-chapter-icons.py          # bakes the 24 pins into index.html
python3 tools/check-b384-acadpins.py           # and the gates listed in the 384.121 notes
```

Then `tools/check-b384-badges2.py --class academy` turns red on purpose (it holds the academy to main's flat badges): retire it
or point it elsewhere. The notes (`### 384.121 (badges)` in `docs/notes-archive.md`) say what each pin is and the decision left
open then: a pin shows no dirt, so the dirty-badge stages no longer show on an academy badge drawn as a pin.
