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

## Object values that are readable

From the switch in `0x528040`. Object type numbers are the map format's.

| Object | Value |
|---|---|
| Artifact (5) | The artifact's own value, at least 10. Only if the backpack has room. Variants: needs 2000 gold; needs Wisdom; needs Leadership; needs 2500 gold and 3 of a resource; needs 3000 gold and 5 of a resource; guarded, where the fight value is added. A requirement the hero cannot meet makes the value 0 |
| Pandora's Box (6) | Fight value of its guards, plus its experience, skills, spells the hero can learn, resources and `AI Value × count` of its creatures |
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

Not read yet: dwellings, towns, enemy heroes, shrines, wells, teleporters and most of the remaining cases, which sit in their own routines.

## Hiring heroes

`0x431360`. A computer player does not hire when any of these holds:

- it has more than 7 heroes, or less than 2500 gold;
- it already has the per-difficulty maximum: **Easy 2, Normal 3, Hard 4, Expert 5, Impossible 6** (table `0x660518`);
- it has at least one hero and all computer players together have reached **Easy 8, Normal 11, Hard 14, Expert 17, Impossible 20** heroes (table `0x66052c`).

Which hero it picks in the tavern is not decoded yet.

## Not decoded yet

- Most object values, and the numeric weights inside the ones listed (experience, resources, spells).
- The fight simulator `0x426bc0` itself.
- Hero roles (main hero, scouts, gatherers), army transfers between heroes and towns, when a hero returns to defend a town.
- Adventure spells (Town Portal, Dimension Door, Fly, Water Walk) and boats.
- Danger flags on paths.
