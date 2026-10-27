# The cracked planet (retired in build 337)

Madison: *"The whole 'cracked planet thing' we are not gonna do that anymore. Makes the story line confusing
for no reason. Remove it, remove it from cutscenes and the story line completely. No more cracked planet, you
don't get a cracked planet."*

## What it was
- **A crack that grew with the rank** on Home's planet, from Gold to Supernova (`CRACK_RANK_STAGE`, `CRACK_STAGES`,
  `heroCrackStage`, `cosmicScarArt(stage)`, `drawScarArt`, `buildCosmicScar`, `decorateCrackHero`), with a seam of
  light in it from Platinum (`scarSeam`).
- **The Supernova scar** on a Supernova account's planet (`decorateSupernovaHero`): the burn, its fragments, the
  motes drawn into the rings (`scarMotes`), the debris riding the rings (`addRingDebris`), the soot on the rings and
  the veils over secret flares (`scarPassEffects`).
- **In the cutscenes:** the crack forming after each rank's flash (`crackFormArm`, `rank.crack`), the fracture
  running across the planet in Supernova's swell (`.sn-fracture`), the scar coming up through the dust
  (`sn-scarred`), the debris thrown out into orbit (`snSweep`).
- **In the story:** Nova's planet-explosion scene (`buildNovaWreck`, sound `cs.planet`), the strain planet
  (`novaStrainPlanet`), and the lines saying a planet cracks as you climb and badges hold it together (the rank-up
  talk, his rank messages, the chat's planet answer, the Gold rank lore).

## What stayed
The Supernova rank-up scene itself (the planet swells and heats, the flash, the shockwaves, the dust and flung
shards, the rings turning orange), Home's orange rings for a Supernova account, Nova's voyage (the storm tears his
ship apart; his badges, flares and crew are scattered), and every other "crack" in the app: the badge case's lid, the
special flare scenes, the characters' own art.

## Putting it back
The removal is one commit that touches only `index.html`:

```
git revert 85862e3        # (the hash of build 337's removal commit, as merged)
```

If later work has touched the same lines: `git apply -R --3way retired/cracked-planet.patch`. Then bump
`APP_BUILD` and `version.json` together, restore the gates from the commit before (the sections of
`check-behaviour.py`, `check-b325-c.py`, `check-b326-c.py`, `check-b327-e.py` that measured it, and the sound names in
`check-sound.py`) and re-add the retired lines of story text from the patch.
