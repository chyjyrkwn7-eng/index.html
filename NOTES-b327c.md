### Build 327 (b327c) - Nova's story with a reason, the recap ends on the class, repeat podium finishers, Final Exams, a calmer course card

Madison, Oct 20:
*"In the weekly recap, why are we are calling it to the this week board?
Fix that. The weekly recap, I like it all up until the point after the
class combined [hundos] and combined study time, because it mentioned more
honorable mentions but that section was over with? So it needs to end with
the class time and hundos and tests completed and then that's it. If
someone manages to get top 3 more than once or back to back mention that
during the podium presentation part too."*
*"Calendar is looking good, where it says the date of when the test got
posted, don't include that? The orange dot, it says big exam, and pt
final. It can be more than that though. Final Exams is probably what the
name should be for it. On the calendar, it says, on the test, ensure that
part is only there if we have the information ... some of the colors in
'the course' box look confusing because it's so many."*
*"Meeting nova, he starts to explain the cracking, 'every flare you light
pours its light into your planet, it can't hold it all..' ... I don't like
this one at all."* *"The badge explanation is bad at the end, it says
something about finding them so I can teach you that unit? That's
terrible."* *"The storyline is still not great, we need to understand why
your planet blew up, what the badges and stuff are, and why we should
avoid cracking ours kinda thing."*

Branch: builder C's worktree off `wip/build-326` (5ce026a). Gate:
`tools/check-b327-c.py` (`ONLY=recap,cal,story,issues`; 41 checks, all
pass here; 33 fail on 326 - the eight that pass on both are guards: no
claim without a record, a known topic still shown, the line counts).

#### Nova's story (supersedes 326's "pours its light / becoming a star / a page of my log")

**The story is the app's own rules, said once each:**
- **The planet his ship was studying had taken in more light than it could
  hold**, with nothing holding it together. It cracked, its core gave way,
  it exploded, and the blast scattered his flares, badges and crew.
- **A badge is a unit mastered** - that unit's hundos
  (`badgeThresholdFor`) - and **badges are what hold a planet together.**
  Never "so I can teach you that unit", never a page of his log.
- **Your planet cracks from Gold up, a little more every rank**
  (`CRACK_RANK_STAGE`): the strain of holding a brighter flare. It never
  goes the way his did because **every rank asks for badges** and **your
  level waits at your next rank's level until you have its badges**
  (`levelWallOf`). That is why you keep finding badges - not a warning to
  stop climbing (the cracks cannot be avoided in the app: ranking up makes
  them, and nothing repairs them).
- **At Supernova it has held all of his light and become a star**, as the
  rank-up message and the lore already said.

**The introduction, new account (16 lines, as on 326):**
1. Hello, *Name*! I'm Nova, an explorer and an instructor. I'll be your guide here, and I need your help. *(his name)*
2. Not long ago, my ship was studying a planet much like the one on your Home screen. It had taken in more light than it could hold, and it had started to crack. *(the wreck)*
3. Then its core gave way, and the whole planet exploded. The blast tore through my ship and threw everything aboard across this system. *(the wreck, exploding)*
4. My flares, one for each rank, came to rest around your planet, but the blast had put their light out. That's why the flares on your Home screen are dark. *(his flares, dark)*
5. Some of my secret flares were thrown further out, into your tests. I've lost count of them, so keep your eyes open. *(the flares, still - moved here so it keeps a picture that matches)*
6. A flare only lights again for someone who has earned it. Every rank you reach relights one, and each comes with my thanks: that rank's rewards. *(the rank emblems)*
7. My badges landed one in every unit. A badge means you've mastered that unit: score a hundo on the whole unit enough times, and it's yours. *(every unit's badge)*
8. Your planet is a lot like that one. From Gold up, every rank you reach will put a crack in it: the strain of holding a brighter flare. Badges are what hold a planet together. The one I was studying had none. *(NEW picture: Home's planet with Sapphire's crack, `novaStrainPlanet()`, "A crack for every rank from Gold")*
9. So every rank asks for badges as well as a level. Right answers earn XP and XP raises your level, but your level waits at your next rank until you have its badges. That way your planet never takes in more than it can hold, all the way to Supernova. *(the XP bar)*
10. My crew got away in escape pods and landed all over this system. They're the characters in this app, and every one you find joins you. *(the crew)*
11. Each one comes home a different way: some with a rank, most with a challenge, a few behind a secret flare, and the ultimate ones ask for nearly everything else first. *(how they come home)*
12. As thanks, I'll hand you things along the way: banners for your profile, and effects that play when you score a hundo. You earn them by studying, and they're all in Customize, on your Profile. *(banners and effects)*
13. Drill to learn a unit, the Qualifier to prove you're ready, and Review to go over the material first. Or take any of them into a Virtual Room. *(the modes)*
14. You don't have to do it alone, either. In a Virtual Room you can race your classmates, and you can challenge me there too. *(the Virtual Room)*
15. One more thing: I've added you as a friend. When I have news for you, I'll send it to your chats, up there. *(his chat row)*
16. So that's the job: light my flares, find my badges and bring my crew home. My scanners keep finding more of my ship, so there will always be more. Let me show you around.

**An existing account (21 lines with the level note, as on 326):** "There
you are, *Name*. I'm Nova ... I don't think we've met." / "I've been
following your progress, and you've already found some of what I lost.
Let me tell you how I lost it." then lines 2-14 above (line 4 reads
"They're the flares on your Home screen" and line 6 "you've already lit
*N*" once they hold a rank), the recap of what they have
(`novaRecapLines`), the friend line, and "A few things have changed
around here, too. Let me show you what's new."

**The old line 9** ("You'll do all of it by studying ... your level and
badges decide your rank") is folded into the new line 9, and the
pictureless "pours its light" line is gone, so the count is unchanged.

**Everywhere else he tells it, the same story:**
- Goodbye: "Light my flares, find my badges and bring my crew home, and
  your badges will keep your planet whole while you climb."
- Rank-ups (`NOVA_RANK_HEAD`): Gold "your planet has started to crack
  under its light. That's the strain the planet I was studying showed,
  but yours has your badges holding it together. Keep finding them.";
  Platinum "The crack in your planet is wider now, and your badges are
  holding it."; Sapphire "Your planet carries more light than ever, and
  it's holding."; Supernova "your planet has held all of my light, and it
  has become a star." Bronze, Silver, Amethyst unchanged.
- Badge messages: "You found my *Unit* badge ... You've mastered *Unit*,
  and that's one more badge holding your planet together." (and two
  other wordings); several: "That's *N* units mastered, and your planet
  is stronger for every one."
- Chat replies (planet, badges, rewards, flares), the Version 9 "Nova,
  Your Instructor" note, standalone What's New's story line, the
  returning planet tip, and Gold's Rank-tab lore ("starts to crack under
  Nova's light, and where your badges start to matter most: they are what
  hold it together").
- Canon comments rewritten above `novaIntroLines` and `NOVA_RANK_HEAD`.

#### HANDOFF-326 known issues
1. **A badge found with a rank-up is named now.** `novaProgressTail`
   returned only the FIRST other kind found, so rank + crew + badge named
   the crew and dropped the badge (which was then marked said). It now
   names every kind not yet said, by name, in one sentence: "On the way,
   Detective came home and you found my Penal Code badge, too." (secret
   flares by name too).
2. **The returning Profile tip** no longer says "your badge case opens from
   it" (What's New lost the badge case's row in 326).
3. Left alone, as asked (the crew slide's count).
4. Not looked into (two frames between the badge and crew slides) - likely
   the recorder; the badge/crew slides are made ahead as before.

#### The weekly recap
- **"Last week's board", never "the This Week board"**: the hello is
  "First, the top three on last week's board." (The unlock notes for Zeus
  and Poseidon still say "the This Week board" - that is the tab's name
  and they mean the live board; left.)
- **It ends on the class**: one last line, final, with the sign-off in it -
  "And the whole class, together last week: 15 hundos, 53 tests finished
  and 27 hours on the study clock. That's the week. See you all next
  Tuesday." The class's page (the last page) has three tiles: hundos,
  tests, studied. `weekRecapClassWeek` totals `t` as well as `h` and `m`,
  each only off the rows that report it (>= 3 rows and 60% of last
  week's active rows, as before).
- **Gone after it**: the "This week so far" closing line and its card
  (`weekRecapClose` is kept, unused; `r.close` is null), and the separate
  goodbye line.
- **The two awards (Flawless, Long Shift) ARE honorable mentions** and are
  said with them: "Now, from off the podium, my honorable mentions" counts
  them, the rotating mentions play, then the awards on their own page
  (`.wr-page-awards`, headed "Honorable mentions / Off the podium"), then
  the class. Same rules for who can win them as 326.
- **"As for you" (your place, if you were not named) moved before the
  class's line**, so the class stays last.
- **Repeat podium finishers** (`weekRecapPodiumHistory`,
  `weekRecapAgainSay`): in the podium line - "Bo was on the podium the
  week before, too: back to back." / "That's three weeks running on the
  podium for Bo." / "That's Cy's second time on the podium." / "Cy has
  been on the podium before." - and a small tag over the avatar ("Back to
  back" / "Again"). **Only from weeks whose podium is known**:
  `WEEK_RESULTS_KNOWN` (the hand-recorded 21 Sep week) and this device's
  own recaps, which now record the whole podium (`hist[week].top`; kept 12
  weeks). Recaps from 324-326 recorded only the winner (`win`): that
  counts for the winner and claims nothing about second or third. **The
  live top-three cache (`class26e.weektop.v1`) is not used** - it is the
  board mid-week, not where it ended. An exact count ("second time",
  "three weeks running") is said only when every week in range is fully
  known; otherwise the softer true sentence. A winner whose story is
  already "for the second week running" gets no second mention.
- **What this means in practice**: until devices have recapped a few
  weeks on 327, the history is thin - mostly winners and the 21 Sep week -
  so most weeks will say nothing extra. It never says something it does
  not know.

#### The Calendar
- **No "Posted <date>"** on the topics (postedAt stays in `TEST_TOPICS`,
  unshown).
- **"On the test" only when the topics are known**: no "Not posted yet"
  box; a test with no `TEST_TOPICS` entry has no topics part at all.
- **"Final Exams"**: the orange key entry and the card's heading (was "Big
  exam / PT final" and "Big exams & PT finals"); the chips say "Final exam"
  ("Final exam · Level One Final" on the day card), Today "Final exam
  day"; PT finals keep their own name on their row and chip. The code's
  names (`isBigExamDay`, `cal-cell-dot-big`) did not change.
- **The course card in two colours that mean something**: blue = class
  days (the ring and "Class days left", the same `#6FC2FF`), amber = tests
  (the calendar's test-dot `#F5B54D`), "Days to graduation" plain white.
  It was a blue ring with blue, amber and gold numbers.
- **The boxes were left as they are** ("I like the boxes"); see open
  decisions.

#### Gates
- `tools/check-b327-c.py` - new (above).
- `check-b326-g.py`: the recap's ending (the class's totals, not "this
  week so far"), the awards measured on their own page and three tiles on
  the class's page, the key's orange entry "Final Exams".
- `check-b326-e.py`: the planet line (badges hold it, no "pours"), what
  you get (a badge is a unit mastered, no log), the chat replies, the
  Version 9 note, standalone What's New, the planet tip, the progress
  messages.

#### Open decisions for Madison
- **The recap's goodbye is inside the class's line** ("... That's the
  week. See you all next Tuesday."), so nothing comes after the totals. If
  "that's it" meant no goodbye at all, drop the last two sentences.
- **"As for you" moved before the class's line** rather than being cut.
- **The calendar's boxes**: same number of boxes. If it still feels busy,
  the cheapest next step is folding "This week" into the Today card, or
  putting The course behind its existing switch by default.
- **"Final Exams" in title case** (her words) beside "Class day" / "No
  class" in sentence case on the key.
- **The story's premise for "why avoid cracking ours"**: in the app the
  cracks can't be avoided - every rank from Gold makes one, and nothing
  repairs them - so he says the cracks are strain and badges are what keep
  the planet whole. If she wants cracks that can actually get WORSE (e.g.
  from levelling without badges), that is a mechanic change, not copy.
