---
title: "AI: adventure map"
parent: English
nav_order: 11
lang: en
---

# AI: adventure map decisions
{: .no_toc }

How a computer player's hero picks where to go. First version: the structure and the rules that survived decompilation cleanly. Much of the per-object arithmetic is floating-point code that the decompiler dropped; those parts are listed at the end.

1. TOC
{:toc}

## Summary

- Every object the hero can reach gets a **value**. Fights are valued by simulating them.
- Values are spread onto nearby tiles, so a cluster of small pickups can outweigh one larger object.
- The score of a destination is its value divided by the path cost, but anything worthwhile **within about a fifth of a day's movement is taken first, nearest first**.
- A hero keeps its previous target unless something clearly better appears.
- Difficulty changes how many heroes the AI hires, how strong it thinks a human army is, and whether it prefers to take from humans or from other computer players.

## Step 1: list the targets

Path costs below are in the movement points described in [Adventure map](../adventure/). Fights that the hero takes are settled by the rules in [battles without a battlefield](../ai-battle/#battles-without-a-battlefield) unless a human is involved.

`0x42edd0` walks the hero's pathfinding result and asks `0x528040` for the value of each tile that holds an object.

- A value of zero or less drops the target.
- A tile the player **has not explored** is not evaluated; it gets a flat value of 100. Exploration is therefore a weak default pull that any real object beats. **[code]**
- If the hero stands in a town with a garrison hero slot conflict, or the destination belongs to an ally, the target is skipped.

## Step 2: spread the values

`0x42e0b0`, first loop. For each target in explored territory the pathfinder is run outwards from the target, and every tile it reaches receives

```
share = target value × 300 / (extra path cost + 300)
```

added into a per-tile map. A tile 300 movement points away from an object gets half of that object's value. **[code; the exact origin of "extra path cost" is simplified here]**

## Step 3: total value of a candidate

`0x42f980`:

```
total = spread value at the tile + the object's own value + the fight value for its guards
```

- If this is the target the hero chose on its previous step (kept in the hero record), 20 is added and no randomness is applied.
- Otherwise a positive total is multiplied by a random 76 to 100 percent (`rand(1,25) + 75`).

## Step 4: choose

`0x42e0b0`, second loop.

```
score = total                        if path cost <= 100 movement points
      = total × 100 / path cost      otherwise
```

A candidate is **near** when its path cost is at most 21% of the hero's full daily movement and the path is not flagged as dangerous.

1. A near candidate beats every candidate that is not near, whatever the scores.
2. Among near candidates the smaller path cost wins; equal cost falls back to the higher score.
3. Among the rest the higher score wins.

So an AI hero sweeps up everything close before it sets off for a distant, more valuable target. **[code]**

## Who the AI goes after

`0x527960` sets two numbers each turn from the game difficulty, and `0x428710` returns one of them for the owner of whatever is being valued:

| Difficulty | Owner is a human player | Owner is another computer player | Unowned |
|---|---|---|---|
| Easy | **−0.4** | 1.0 | 0 |
| Normal | 0.5 | 0.5 | 0 |
| Hard | 0.75 | 0.25 | 0 |
| Expert | 1.0 | 0 | 0 |
| Impossible | 1.25 | **−0.25** | 0 |

Formula above Easy: human `(difficulty + 1) × 0.25`, computer `0.75 − difficulty × 0.25`, with difficulty 1 to 4. **[code]**

The factor is used when valuing mines, in the fight valuation when the opponent belongs to a player, and in two more places in the object switch that were not read (`0x528040`, `0x529cb0`).

- On **Easy** taking something from a human is worth less than taking the same thing unowned, and computer players prefer each other's property.
- As difficulty rises the preference turns around. On **Expert** another computer player's ownership adds nothing; on **Impossible** it subtracts, so computer players leave each other alone and concentrate on humans.

**Where the hero is hired** (`0x431800`). The new hero's immediate worth is the value of its artifacts plus its starting army priced at the resource weights. If that is below a threshold tied to the 2500 gold price and the player does not hold at least `2500 × its number of heroes`, nothing is hired. Otherwise every town of the player with no visiting hero is tried: a town needs a Tavern, or one that can be built that day, in which case the Tavern's cost at the resource weights is subtracted. To this is added what the new hero could reach from that town (`0x431bd0`, the same target evaluation as for any hero). The town with the best total gets the hero. **[code; the exact threshold expression was not read]**

## Adventure spells in path planning

The computer does not decide "now I cast Town Portal" as a separate step. The spell is an extra **edge in the hero's pathfinding graph** (`0x56b050`, called from the pathfinder `0x56b440`), so a destination reached through a portal is scored like any other, by value over path cost.

### Town Portal

Considered when the hero knows the spell, has not already used a portal earlier on the same path, and has **mana for the spell plus 20 to spare**.

| School level | Destinations offered |
|---|---|
| none, Basic | only the nearest of the player's towns on the same map level (straight-line distance), and only if no hero is visiting it |
| Advanced, Expert | every town of the player that has no visiting hero |

The edge costs **300 movement points, or 200 at Expert**, matching what the spell charges, plus a distance-based term the pathfinder uses to order its search.

### Castle Gate

`0x56a850` adds the same kind of edge for Inferno's Castle Gate. From an Inferno town of the hero's own side, every other Inferno town of the player that has no visiting hero is a destination at **no movement cost**.

A missing gate does not rule the route out: if the Castle Gate can be built today and the player can afford it, the edge is still offered, with the building's cost at the [resource weights](#what-resources-are-worth) counted against the destination's value. The routine allows for building up to two gates (one at each end) this way.

### Monoliths, gates and whirlpools

These objects have no value of their own in the object switch. In the pathfinder (`0x56ab40`) they are edges, like Town Portal and Castle Gate, so the computer uses them whenever they shorten the way to something it wants:

| Object | Edge |
|---|---|
| One-way Monolith entrance (43) | to the exits (44) of the same kind |
| Two-way Monolith (45) | to the other two-way monoliths of the same kind |
| Subterranean Gate (103) | to its paired gate on the other level |
| Whirlpool (111) | to the other whirlpools |

Whether the pathfinder charges anything for the army a Whirlpool takes was not read. **[code]**

### Boats

In the same routine that handles objects along a path (`0x56ab40`), a **boat on the map** is a switch between walking and sailing rather than a destination with a value of its own:

- it is used only in the full planning mode and at most once per path;
- stepping onto it ends the land leg, and what the hero can still spend is replaced by its sea allowance (see [movement at sea](../adventure/#at-sea)).

So a computer hero will board a boat that lies on the way to something valuable across water. A Shipyard or Lighthouse not owned by its side is worth a flat 1000 as a target. Building a ship at a Shipyard and casting Summon Boat were not found in the routines read. **[code for the boat case; the reading of the movement swap is inferred]**

### Fly and Water Walk

The pathfinder lets a hero cross water or obstacles when the effect is available: artifact 72 (Angel Wings) or 90 (Boots of Levitation), an already active spell, or, for Water Walk, knowing the spell. Step costs are the ones in [cost of a step](../adventure/#cost-of-a-step). **Fly and Dimension Door are probably never cast by the computer.** The pathfinder tests "knows Water Walk" and "knows Town Portal" by reading fixed fields of the hero record. A search of the whole decompiled executable finds no such test for the Fly field at all, and none for the Dimension Door field in any hero or pathfinding routine. **[unverified: this is the absence of a match in a search, and a spell reached through a computed index would not show up]**

**[code]**

## Valuing a fight

`0x427330` is used for guards, wandering stacks, banks, garrisons and enemy heroes.

1. Both armies are turned into strength records (`0x423ee0`) with a multiplier:

   | Side | Multiplier |
   |---|---|
   | The AI's own army | a per-hero factor stored in the hero record, **[inferred]** to be the class `Aggression` from [the hero class table](../heroes/) (1.0 for might classes, lower for most magic classes); halved when the scenario is lost if this hero dies |
   | Opponent: neutral or another computer player | 1.25 |
   | Opponent: a human player's army or hero | by difficulty: Easy 0.5, Normal 0.5, Hard 1.0, Expert 1.25, Impossible 1.25 (table `0x6604d0`) |

2. The fight is simulated (`0x426bc0`). If the AI cannot win, the value is −1,000,000,000 and the target is unusable.
3. Otherwise `value = gain − AI Value of the units expected to die`. A small negative result is rounded up to 0 when the expected losses are under a quarter of the army.
4. Killing a hero that is a victory or loss condition adds 5,000,000.

On Easy and Normal the AI treats a human army as **half** as strong as it is, so it attacks players it cannot beat. On Expert and Impossible it is as cautious with humans as with anyone else. **[code]**

## What resources are worth

`0x428740` recomputes, every turn, a value for one unit of each of the seven resources for each computer player. Every object value and every purchase decision below is expressed through these weights, so they are the AI's exchange rate between gold, materials and army.

```
have[r] = stock + 2 × daily income
need[r] = largest cost of any single building the player's towns can build now
        + cost of buying everything available of its three best creature types
          (ranked by AI Value × number available; from day 5 the coming week's growth is counted too)

base = market factor, by the number of the player's towns with a Marketplace:
       0 or 1 → 0.10, 2 → 0.15, 3 → 0.20, 4 → 0.25, … 9 or more → 0.50      (table 0x678344)

w = base                                         if need = 0
  = min(need / have, 1 / base)                   if have < need
  = ((have − need) × base + need) / have         otherwise

weight[r] = nominal price[r] × w
```

Nominal prices (table `0x68c482`): wood 250, ore 250, mercury 500, sulfur 500, crystal 500, gems 500, gold 1.

- A resource the player has in surplus is worth only 10–50% of its nominal price. More Marketplaces raise that floor.
- A resource the player is short of is worth up to `1 / base` times nominal, so up to ten times with one Marketplace.
- Gold follows the same rule. An AI that cannot afford its next building values gold above 1 per coin.

**[code; the "have < need" branch divides only when `have > 1`]**

## Per-hero and per-player figures

`0x527760` and `0x527960`, recomputed each turn:

| Figure | Formula |
|---|---|
| Hero's value of one experience point | `(2500 + AI Value of the hero's army) / (40 × experience needed for the next level)`. A whole level is therefore worth one fortieth of "price of a hero plus its army" |
| Hero's value of a Spell Power point | Gain in the hero's total spell value (`0x5275b0`) from +1 Spell Power, at least 10 |
| Hero's value of a Knowledge point | One third of the gain in total spell value from 30 more spell points, at least 10 |
| Player's artifact-worth figure | Average value, for this player's heroes, of all artifacts that are enabled on the map |

### What an artifact is worth

`0x4336c0` and `0x4339e0`. The artifacts themselves are listed under [Artifacts](../artifacts/). Each artifact carries a list of effect evaluators; the artifact's value **for a given hero** is the sum of what those evaluators return for that hero, so the same artifact is worth different amounts to a might hero and a caster. Parts of a combination add the combination's evaluators as well. An artifact named in the scenario's victory condition gets a large bonus. War machines have their own formulas; the Ballista's uses the hero's Attack and Artillery.

Wherever a routine needs a value "for the player" rather than for one hero, it takes the best value over the player's heroes, with a floor of 10 (`0x433aa0`). This is the number used for artifacts on the map, in chests, at merchants, in the [tavern choice](#hiring-heroes) and in the [exchange between two heroes](../ai-towns/#when-a-hero-visits-its-own-town). The individual effect evaluators were not read. **[code]**

## Object values that are readable

From the switch in `0x528040`. Object type numbers are the map format's.

| Object | Value |
|---|---|
| Artifact (5) | The artifact's own value, at least 10. Only if the backpack has room. Variants: needs 2000 gold; needs Wisdom; needs Leadership; needs 2500 gold and 3 of a resource; needs 3000 gold and 5 of a resource; guarded, where the fight value is added. A requirement the hero cannot meet makes the value 0 |
| Pandora's Box (6) | Fight value of its guards, plus its experience, skills, spells the hero can learn, resources and `AI Value × count` of its creatures |
| Black Market (7) | Only if the backpack has room. Sum over its seven artifacts of `artifact value − price at the resource weights`, counting only artifacts the player can pay for and only positive differences |
| Creature dwelling (17, 20) | 0 if it belongs to an ally. Otherwise the fight value for its guards if it is not the player's own, plus the [army gain](../ai-towns/#the-gain-of-adding-a-stack) from recruiting what is waiting there with the resources the player has now. For a dwelling the player already owns, the value is dropped to 0 when the path is 400 points or longer and the gain is under a third of the hero's army value. If the victory condition is to flag all dwellings, 5,000,000 divided by the number of dwellings is added for one not yet owned (`0x529a30`) |
| Shrine of Magic (88–90) | The value of its spell to this hero (`0x527640`), if the hero has a spell book, does not know the spell, and the spell's level is at most `Wisdom level + 2`; otherwise 0 |
| Magic Well (49) | The hero's stored value of a full mana refill, if not already used. Dropped to 0 when the path is over 300 points, unless the hero was already heading for a well or spring |
| Star Axis (61) | The hero's value of a Spell Power point, if not visited |
| Pyramid (63) | 0 if this player already took it. Otherwise the fight against its guards (40 Gold Golems and 20 Diamond Golems), plus, for a hero with Expert Wisdom and a spell book, the average value of the level 5 spells it does not know |
| Prison (62) | 0 if the player already has eight heroes; otherwise a value from the prisoner's army |
| Keymaster's Tent (10) | 5000 if this player has not visited that colour, otherwise 0 |
| Campfire (12) | Proportional to the amount it holds |
| Creature Bank (16), Derelict Ship (24), Dragon Utopia (25) | If not already cleared: fight value against the stored guards, plus the stored resources, plus `AI Value × count` of reward creatures, plus the artifacts. See [creature banks](../ai-neutral/#creature-banks) |
| Garden of Revelation (32) | A per-hero "value of one primary skill point" kept in the hero record, if not visited |
| Corpse (22) | Not yet searched by this player: one fifth of a per-player "artifact worth" figure; if the backpack is full, 200 gold at the gold weight |
| Marletto Tower (23) | Not visited by this hero: experience needed for the hero's next level × the hero's value of one experience point |
| Arena (4) | Not visited: twice that |
| Flotsam (29) | 175 gold + 5 wood at the current weights (its average contents) |
| Mystical Garden (55) | If it has something this week: `(500 gold + 5 gems) / 2` at the current weights |
| Learning Stone (100) | Not visited by this hero: `1000 ×` the hero's value of one experience point |
| Mine (53) | Not if it already belongs to the AI's team. `2 × daily output × resource weight × (1 + owner factor)`, plus the fight value for its guards. Daily outputs in the executable: wood 2, ore 2, the four rare resources 1, gold 1000. If the victory condition is to flag all mines, 5,000,000 divided by the number of mines is added |
| Resource pile (79) | `amount × resource weight`, plus the fight value for its guards |
| Wandering monsters (54) | The fight value alone; +5,000,000 if this stack is the scenario's target |
| Treasure Chest (101) | Sum over the three chest sizes of the better option, weighted by their odds: `max(160 × exp value, 320 × gold weight) + max(320 × exp value, 480 × gold weight) + max(465 × exp value, 620 × gold weight)`, plus one twentieth of the artifact-worth figure. The constants are 32%, 32% and 31% of 500/1000, 1000/1500 and 1500/2000 |
| Lighthouse (42), Shipyard (87) | 1000 if not owned by the AI's side, otherwise 0 |
| Unexplored tile | 100 |

Towns and heroes are covered in the next section. Teleporters are path edges, see [monoliths, gates and whirlpools](#monoliths-gates-and-whirlpools). Not read yet: stat boosters other than those listed and the remaining minor cases, which sit in their own routines.

## Towns and heroes as targets

### Capturing a town

`0x529cb0`, for a town that belongs to nobody or to an enemy.

```
value = fight value against the garrison
      + ( 3 × the town's daily gold × gold weight
        + its Resource Silo output at the resource weights
        + the creatures waiting in its dwellings, at their purchase cost in resource weights
          (next week's growth too, if the hero would arrive after day 7)
        ) × (1 + owner factor)
      + 5,000,000 / number of towns on the map
```

- If the computer player owns **no town at all**, the last term is the full 5,000,000, and an unwinnable garrison no longer rules the target out: it only subtracts 2,500,000.
- If losing that town is the opponent's loss condition, another 5,000,000 is added.

Ordinary objects are worth hundreds or thousands, so a reachable, winnable town outranks almost anything else on the map; what holds the AI back is the fight estimate and the distance divisor.

### Its own towns

`0x52ab80`. Visiting a town of its own is worth what the hero would gain there: recruits (`0x52b090`) and the visit itself (`0x52b1e0`), plus the Grail's value if the hero carries it and the town can take it.

A town carries a **threat mark**, a counter in the town record ([how it is set](#how-a-town-gets-its-threat-mark)). When it is above zero, the town is worth an extra `5,000,000 / number of towns` to its owner's heroes, or the full 5,000,000 if holding it is a victory condition. This is what pulls heroes home to defend. Above Easy, and when the player has more than one hero, the same bonus is applied only to a hero that is not clearly weaker than the one already inside.

### How a town gets its threat mark

`0x4280e0`, run twice at the start of each computer player's economy phase (`0x428dd0`), before anything is built.

For every hero of every enemy player:

1. Run that hero's pathfinding with a budget of **its daily movement plus 800 points**.
2. For each of the computer player's towns inside that range, simulate the enemy army attacking the garrison (`0x428410`), with the attacker's strength at ×1.25 and the garrison's at ×0.75. If the attacker wins, the town counts as in danger.

The two passes do different things with a town in danger:

| Pass | Action |
|---|---|
| First | Buy the creatures available in that town straight into its garrison (`0x428580`) |
| Second | Clear every town's mark, then add 1 to the mark of each town still in danger after those purchases (`0x428570`) |

So the mark is a count of enemy heroes that can reach the town within about a day and a half and are expected to take it. A town whose garrison was saved by the emergency purchase is not marked.

The same routine tags the **enemy hero**: it stores `5,000,000 / number of the computer player's towns` in that hero's record. This is the "term for the hero itself" below, so a hero threatening a town becomes a very valuable target as well. **[code]**

### Enemy heroes

| Situation | Value |
|---|---|
| Enemy hero | The fight value. If it can be reached this turn, `(threat value stored on that hero + 10000) ×` the owner factor is added. The stored value is `5,000,000 / number of the AI's towns` for a hero that threatens a town, otherwise 0 |
| Enemy hero standing in a town | The above plus the capture value of the town. With no town of its own, the AI still considers an unwinnable fight, at −1,250,000 |
| Hero of the same player, above Easy | The hero with the lower primary skill total hands its army to the stronger one; the value is the gain from merging (`0x42c4a0`), halved when the evaluating hero is the stronger of the two and the other is not within reach this turn |
| Hill Fort (35) | `Σ (AI Value upgraded − AI Value now) × count` over the stacks the player can afford to upgrade |

## Level-up choices

`0x4da720` handles a level-up for every hero; `0x52bbd0` makes the choice for a computer hero.

### What is offered

- The primary skill is rolled first: `rand(1,100)` walked through the class's four chances from [the hero class table](../heroes/) (the first set below level 10, the second from level 10).
- Two secondary skills are then offered: one **upgrade of a skill the hero has** and one **new skill**, each falling back to the other kind when none is available (`0x4dad00`).
- The hero record stores the level at which Wisdom and a magic school were last offered, which is how the engine keeps track of when they are next due.
- The random generator is re-seeded just before the roll, so a given level-up is not re-rolled by reloading. **[inferred: the seeding call is the same `0x50c5f0` as elsewhere]**

### How the computer chooses

- If both offers are the same kind (two new skills, or two upgrades), it takes the one with the higher value from `0x524690`; a tie goes to the first.
- If one is an upgrade and the other is new, the new skill has to earn its slot (`0x524dd0`). The routine ranks, by the same value, every skill the hero does not have and its class can learn, together with the one on offer. The hero has `8 − skills known` free slots; the new skill is taken only if it ranks within that many places from the top. Otherwise the hero takes the upgrade. So a hero with many free slots accepts almost any new skill, and one with a single slot left holds out for the best skill its class can still get.

`0x524690` returns 0 for a skill already at Expert, and for a new skill when the hero already has eight. Otherwise, with `T = 1000 + AI Value of the hero's army` and `S = 500 + AI Value of its shooters`:

| Skill | Value |
|---|---|
| Ballistics | `T / 8` |
| Logistics | `T / 10` |
| Offence, Armorer | `T × 7 / 100` |
| Leadership, Luck, Tactics | `T / 50` |
| Diplomacy | `T / 100` |
| Archery | `S ×` a per-level table value `/ 100` |
| Artillery | `10 × Attack`, and only if the hero has a Ballista |
| Wisdom | `Spell Power × the hero's value of a Spell Power point / 2` |
| Mysticism | a tenth of the hero's value of a Knowledge point |
| Eagle Eye, Scholar | 0 without Wisdom; otherwise small, from Spell Power |
| Fire, Air, Water, Earth Magic | from the hero's spells (`0x524d20`); without Wisdom the simple values are 0, 25, 3 and 30 |
| Pathfinding, Navigation | scaled by the map: the share of land tiles that cost extra to cross, and the share of water tiles, counted once per map by `0x52b9c0` |
| Estates | a per-level table value |
| Intelligence | `Knowledge × the hero's value of a Knowledge point / 4` |
| Sorcery | `Spell Power × the hero's value of a Spell Power point / 20` |
| Resistance | `T / 40` |
| First Aid | 250, and only if the hero has a First Aid Tent |
| Skills not listed (Scouting, Learning and others) | `T / 20` |

Ballistics and Logistics come out on top for a hero with a real army, and army-scaled skills in general beat magic skills unless the hero already has Wisdom and Spell Power. The same ranking test is used when a hero is offered a skill at a Witch Hut or the Magic University. **[code]**

## Obelisks and the Grail

- **Obelisk (57).** Worth `value of the Grail to this player's heroes / number of obelisks on the map` (`0x52a2b0`). It is worth 0 if this player has already visited that obelisk, if the map has no Grail, or if the player already knows where the Grail is.
- **Digging.** Each player record holds a dig position. When it is set, the target builder (`0x42edd0`) adds that tile as a destination like any other, as long as the tile is free and reachable. Its value is the Grail's value to the player's heroes, or 5,000,000 when the scenario's victory condition is to build the Grail. The path cost is raised to at least the hero's full daily movement, which matches the rule that digging takes a whole day.
- A hero carrying the Grail then values a town that can take it accordingly, see [its own towns](#its-own-towns).

**[code]**

### Where the computer decides to dig

`0x52c9b0`, called for a computer player after it visits an obelisk and from its periodic planning (`0x4bae50`, `0x4baed0`).

1. Count the player's revealed puzzle pieces out of 48 (`0x4baf00`): all 48 if every obelisk is visited, otherwise in proportion to obelisks visited, plus any extra pieces the player record holds.
2. Compare the revealed share with a **difficulty threshold** (table `0x6822c8`):

   | Difficulty | Share of the puzzle needed before the computer picks a dig spot |
   |---|---|
   | Easy | more than 100%: it never does |
   | Normal | 50% |
   | Hard | 25% |
   | Expert, Impossible | 0%: from the start |

3. If the share is enough and the map has a Grail, the routine rebuilds the same puzzle picture a human sees, with the unrevealed pieces masking their part of the map, and picks a dig position from the tiles left uncovered around the Grail's place.

The dig action itself (`0x40ec90`) clears the stored position when the attempt cannot be made: the hero has already moved that day, its backpack is full, or the tile cannot be dug. **[code; how the spot is chosen among the uncovered tiles, and so how accurate an Expert computer's first guess is, was not read]**

## Hiring heroes

`0x431360`. A computer player does not hire when any of these holds:

- it has more than 7 heroes, or less than 2500 gold;
- it already has the per-difficulty maximum: **Easy 2, Normal 3, Hard 4, Expert 5, Impossible 6** (table `0x660518`);
- it has at least one hero and all computer players together have reached **Easy 8, Normal 11, Hard 14, Expert 17, Impossible 20** heroes (table `0x66052c`).

**Which of the two tavern heroes:** for each, the routine adds up the value of every artifact the hero carries or wears, valuing each artifact by how useful it would be to the best-suited hero the player already has (at least 10 each). It hires the one with the larger total; if the totals are equal, the one with the higher sum of primary skills. Class, specialty and starting army are not compared. **[code `0x431360`]**

## Not decoded yet

- Most object values, and the numeric weights inside the ones listed (experience, resources, spells).
- The fight simulator `0x426bc0` itself.
- Hero roles (main hero, scouts, gatherers), army transfers between heroes and towns, when a hero returns to defend a town.
- Building ships.
- Danger flags on paths.
