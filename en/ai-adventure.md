---
title: "AI: adventure map"
parent: English
nav_order: 11
lang: en
---

# AI: adventure map decisions
{: .no_toc }

How a computer player's hero picks where to go. Floating-point parts of the per-object arithmetic were read from the assembly.

1. TOC
{:toc}

## Summary

- Every object the hero can reach gets a **value**. Fights are valued by simulating them.
- Values are spread onto nearby tiles, so a cluster of small pickups can outweigh one larger object.
- The score of a destination is its value divided by the path cost, but anything worthwhile **within about a fifth of a day's movement is taken first, nearest first**.
- A hero keeps its previous target unless something clearly better appears.
- Difficulty changes how many heroes the AI hires, how strong it thinks a human army is, and whether it prefers to take from humans or from other computer players.

## A computer player's turn

`0x525e80`:

1. The per-turn difficulty figures are set (`0x527960`, see [who the AI goes after](#who-the-ai-goes-after)).
2. **Heroes move**, one at a time, each until it has no movement left or stops (`0x5261f0`).
3. The [economy phase](../ai-towns/#the-economy-phase-of-a-turn): buildings, hiring, resource weights, gifts (`0x428dd0`).
4. **Heroes move again**, including a hero just hired, with the same rule.

**Which hero moves next** (`0x526a90`). Among the player's heroes that have movement points left and have not finished for the day:

1. heroes without a patrol area go before heroes with one;
2. then the hero with the **lowest total of primary skills** goes first. Each skill counts as at least 0 (Attack, Defence) or 1 (Spell Power, Knowledge) and at most 99.

So the weakest heroes move first and the main hero last.

**Patrolling heroes.** A hero placed on the map with a patrol radius keeps its patrol centre (hero record `+0x44`, `+0x45`) and radius (`+0x46`). Such a hero only considers targets on its own map level within that radius of the centre, counted as `|dx| + |dy|` (`0x4e56e0`, used when targets are listed in `0x42edd0` and `0x42f570`). **[code]**

## Step 1: list the targets

Path costs below are in the movement points described in [Adventure map](../adventure/). Fights that the hero takes are settled by the rules in [battles without a battlefield](../ai-battle/#battles-without-a-battlefield) unless a human is involved.

`0x42edd0` walks the hero's pathfinding result and asks `0x528040` for the value of each tile that holds an object.

- A value of zero or less drops the target.
- A tile the player **has not explored** is not evaluated; it gets a flat value of 100. **[code]**
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

**[code]**

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
- On **Expert** another computer player's ownership adds nothing; on **Impossible** it subtracts.

**Where the hero is hired** (`0x431800`). The new hero's immediate worth is the value of its artifacts plus its starting army priced at the resource weights. If that is below a threshold tied to the 2500 gold price and the player does not hold at least `2500 × its number of heroes`, nothing is hired. Otherwise every town of the player with no visiting hero is tried: a town needs a Tavern, or one that can be built that day, in which case the Tavern's cost at the resource weights is subtracted. To this is added what the new hero could reach from that town (`0x431bd0`, the same target evaluation as for any hero). The town with the best total gets the hero. **[code; the exact threshold expression was not read]**

## Adventure spells in path planning

The spell is an extra **edge in the hero's pathfinding graph** (`0x56b050`, called from the pathfinder `0x56b440`). A destination reached through a portal is scored like any other, by value over path cost.

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

These objects have no value of their own in the object switch. In the pathfinder (`0x56ab40`) they are edges, like Town Portal and Castle Gate:

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

A Shipyard or Lighthouse not owned by its side is worth a flat 1000 as a target. **[code for the boat case; the reading of the movement swap is inferred]**

**Getting a boat** (`0x56b440`, `0x4b2300`, `0x42fc50`). The pathfinder may also plan a step from the shore into water where no boat lies. It does so when the hero can cast Summon Boat (below) and no boat is already next to the hero, or when the water hex is a Shipyard's boat hex. When the hero reaches that step:

1. If it can cast **Summon Boat**, it casts it.
2. Otherwise, if the water hex is the boat hex of one of the player's towns that has a Shipyard, or of a Shipyard object the player owns, the computer **buys a boat** there for 1000 gold and 10 wood, if the player has them (`0x430f80`). A town without a Shipyard gets one built on the spot first when it can be built and paid for today.

**Can cast Summon Boat** (`0x4e5550`): the hero knows the spell; its mana is at least the spell's cost at its school level; and there is a boat to move or one can be made. A boat to move is the nearest boat by `|dx| + |dy|` that no hero occupies and that belongs to the player or to nobody. With no such boat, a new one is made only at Advanced or Expert level and only while the map has fewer than 64 boats.

**Casting Summon Boat** (`0x41c8a0`) is the same routine as a human player's cast. For the first free water hex around the hero it rolls 1–100 against the spell's success chance (50, 50, 75, 100 by school level). On success it moves the nearest free boat there, or at Advanced or Expert creates a new one. **[code]**

### Fly, Water Walk and Dimension Door

**Planning** (`0x56b440`, edges in `0x4b2300`). When the hero record is set up for full planning, the pathfinder works out which movement spells are available. The spell-known flags are bytes of the hero record at `+0x430 + spell id`.

| Effect | Available when |
|---|---|
| Fly | Angel Wings (72) worn, or Fly already active, or the hero knows Fly and has **mana for it plus 20** |
| Water Walk | Boots of Levitation (90) worn, or Water Walk already active, or the hero knows it and has mana for it plus 20 |
| Dimension Door | the hero knows it and has mana for it plus 20 |

These edges are offered only for steps that lie within the current day's movement:

- **Dimension Door** is the first choice when a step is blocked: an obstacle, a hex the hero cannot enter, or the edge between land and water. The edge costs 300 movement points, 200 at Expert.
- **Fly** is used for a blocked step when Dimension Door is not available.
- **Leaving land onto water** with no boat: a step that summons or buys a boat (see [Boats](#boats)). Otherwise, if Fly or Water Walk is available, the hero crosses the water with **Fly when its Fly level is higher than its Water Walk level, and with Water Walk otherwise**. The step costs are the ones in [cost of a step](../adventure/#cost-of-a-step).

**Execution** (`0x42fee0`, walking the path step by step):

1. A Town Portal step at the start of the path: the hero is moved, the spell's mana is paid, and 300 movement points are taken (200 at Expert), with the remaining points not going below 0.
2. **Dimension Door** (`0x430ab0`), tried at every step. Conditions: the hero knows the spell; it is not standing on special ground 21 (Cursed Ground by its number); it has mana for the spell plus 20; and it has cast fewer Dimension Doors today than its school level allows (1, 2, 3, 4). With `n = (mana − 20) / cost` casts affordable, at most 6, the jump must save at least this share of the hero's maximum daily movement:

   | n | 1 | 2 | 3 | 4 | 5 | 6 |
   |---|---|---|---|---|---|---|
   | required saving | 1000% | 150% | 100% | 75% | 50% | 25% |

   On a Magic Spring or Magic Well (objects 48, 49) with `n` at least 2, the requirement is 200 points. The landing hex is a later step of today's path within 9 hexes across and 8 hexes down or up, on the same level, not holding an object, and on land or at sea as the hero is. The step with the largest saving is chosen; the spell's mana is paid and the day's count goes up by one.
3. A **Fly** or **Water Walk** step: if the stretch of the path up to the end of today's movement costs more than the hero has left, the hero stops for the day. Otherwise the spell is cast through the same routine a human player uses (`0x4309a0` → `0x41c490`). Nothing is cast when the effect is already active, Angel Wings (or, for Water Walk, Boots of Levitation) are worn, or the hero is in a boat.
4. A Castle Gate step: a missing Castle Gate is built at either end if possible; the move takes 100 movement points (not below 0).

**[code; the cut-off values are from table `0x6604fc`]**

## Danger from enemy heroes

Before a computer hero plans its moves (`0x5261f0`), a **danger map** with one number per map tile is built (`0x42de50`). This happens above Easy, and on Easy only when the computer player is on a team with a human player.

For every hero of every player outside the computer player's team that is still in the game:

1. The [fight value](#valuing-a-fight) of the planning hero attacking that hero's army is computed (`0x427330`).
2. If the value is 0 or more, the enemy hero adds nothing.
3. Otherwise the pathfinder is run from the enemy hero with its movement points plus 300 (`0x56b440`, mode 3). Every tile it can reach gets:
   - **−1,000,000,000** if the planning hero cannot win the fight;
   - the negative fight value added otherwise, so the threats of several enemy heroes add up.

**How the pathfinder uses it** (`0x4b1a70`). A step's danger counts only when the path to it costs more than the hero's movement points left today, that is on tiles the hero would reach on a later day. The danger is then added to the step's search cost, so paths through threatened tiles are taken only when nothing cheaper exists. A step onto a tile marked −1,000,000,000 beyond today's movement is dropped entirely. **[code; the planning call passes the hero's remaining movement as the cut-off (`0x42f570`)]**

## Valuing a fight

`0x427330` is used for guards, wandering stacks, banks, garrisons and enemy heroes.

1. Both armies are turned into strength records (`0x423ee0`) with a multiplier:

   | Side | Multiplier |
   |---|---|
   | The AI's own army | the [hero's own factor](#the-heros-own-factor), from the class `Aggression`; halved when the scenario is lost if this hero dies |
   | Opponent: neutral or another computer player | 1.25 |
   | Opponent: a human player's army or hero | by difficulty: Easy 0.5, Normal 0.5, Hard 1.0, Expert 1.25, Impossible 1.25 (table `0x6604d0`) |

2. The fight is simulated (`0x426bc0`). If the AI cannot win, the value is −1,000,000,000 and the target is unusable.
3. Otherwise `value = gain − AI Value of the units expected to die`. A small negative result is rounded up to 0 when the expected losses are under a quarter of the army.
4. Killing a hero that is a victory or loss condition adds 5,000,000.

On Easy and Normal the AI counts a human army at **half** its strength. On Expert and Impossible the human multiplier equals the one for computer opponents. **[code]**

### The hero's own factor

Every hero carries a personal multiplier that the computer applies to **its own army** in this estimate. It is the only place the per-class `Aggression` column of [the hero class table](../heroes/) is used.

The factor is rolled once, when the hero record is initialised at the start of the game (`0x4d8720`):

```
hero factor = Aggression of the class × rand(75,100) / rand(100,125)
```

The two rolls are independent, so the factor lies between `0.6 × Aggression` and `1.0 × Aggression`. It is stored in the hero record and saved with the game. No other routine that writes it was found; whether the record is initialised again when a defeated hero returns to the tavern pool was not checked.

{% include hero_boldness.html lang="en" %}

Use: in `0x427330` the hero's army strength is multiplied by this factor before the [simulator](../ai-battle/#battles-without-a-battlefield) runs, while the opponent's is multiplied by the values in the table above. A hero with a low factor needs a larger real advantage before a fight is predicted as won. The factor is halved when the scenario is lost if this hero dies.

The factor is read only by this routine. It is not used for human players, in battle, or in any other valuation on this page. **[code and assembly `0x4d8720`, `0x427330`]**

## What resources are worth

`0x428740` recomputes, every turn, a value for one unit of each of the seven resources for each computer player. Every object value and every purchase decision below is expressed through these weights.

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
| Hero's value of one experience point | `(2500 + AI Value of the hero's army) / (40 × experience needed for the next level)` |
| Hero's value of a Spell Power point | Gain in the hero's total spell value (`0x5275b0`) from +1 Spell Power, at least 10 |
| Hero's value of a Knowledge point | One third of the gain in total spell value from 30 more spell points, at least 10 |
| Player's artifact-worth figure | Average value, for this player's heroes, of all artifacts that are enabled on the map |

### What an artifact is worth

`0x4336c0` and `0x4339e0`. The artifacts themselves are listed under [Artifacts](../artifacts/). Each artifact carries a list of effect evaluators; the artifact's value **for a given hero** is the sum of what those evaluators return for that hero, so the same artifact is worth different amounts to a might hero and a caster. Parts of a combination add the combination's evaluators as well. An artifact named in the scenario's victory condition gets a large bonus. War machines have their own formulas; the Ballista's uses the hero's Attack and Artillery.

Wherever a routine needs a value "for the player" rather than for one hero, it takes the best value over the player's heroes, with a floor of 10 (`0x433aa0`). This is the number used for artifacts on the map, in chests, at merchants, in the [tavern choice](#hiring-heroes) and in the [exchange between two heroes](../ai-towns/#when-a-hero-visits-its-own-town). The terms themselves are listed [below](#artifact-effect-terms). **[code]**

### Artifact effect terms

The evaluator lists are data: a table at `0x63ac7c`, loaded by `0x4340e0`, gives each artifact one or more terms out of 24 kinds. The [Artifacts](../artifacts/) page shows the terms of every artifact in the "AI value" column. Symbols:

| Symbol | Meaning |
|---|---|
| `T` | strength of the hero's army (sum of AI values, the same `T` as in the [skill values](#level-up-choices)) |
| `T×n/40` | attack and defence points: 2.5% of the army per unit of `n` |
| `n×SP`, `n×K`, `n×D` | `n` times the hero's stored value of a Spell Power point, a Knowledge point, a round of spell duration |
| `M+n`, `L+n` | morale or luck: `T × 1.73%` for every step gained, counting only steps up to +3. A step that lifts the hero out of negative morale is worth `T × 8.33%` instead, out of negative luck `T × 1.22%` |
| `M−enemy`, `L−enemy` | Spirit of Oppression, Hourglass of the Evil Hour: `T × 3.46%`, minus `T × 1.73%` for every point of positive morale (luck) the hero itself has and would lose |
| `T×n%` | a flat share of the army; used for every effect the authors did not model separately |
| `(T+2500)×n%` | movement artifacts; the constant makes them worth something to a hero with almost no army |
| `Mv×n%` | share of the hero's maximum movement points |
| `T×n% [W]` | mana artifacts; 0 unless the hero has Wisdom and a non-zero Spell Power value |
| `Sh×n%`, `Sh/40` | `Sh` is the summed AI value of the hero's shooters |
| `necro n` | 0 without the Necromancy skill; otherwise `T × p / 250`, where `p` is at most the artifact's `n` percent |
| `orb(school)` | the largest increase in spell value among the damage spells of that school the hero knows, recomputed with Spell Power raised by the table's 100% (the items themselves give +50% damage) **[inferred]** |
| `tome(school)` | the best spell value among the spells of that school the hero does not have |
| `spell n`, `scroll` | the value of that spell to the hero, 0 if the hero already knows it |
| `T/8 [−25×P]`, `T/5 [−50×P]` | Recanter's Cloak and Orb of Inhibition; the bracketed part, Spell Power times 25 or 50, is subtracted when the hero already wears the artifact |
| `3×n×w(res)` | `n` units a day at three times the player's [resource weight](#what-resources-are-worth) |
| `n×AI(Lk)` | `n` creatures of dwelling level `k`: the best AI value among the player's towns that have that dwelling |
| `living/8` | an eighth of the AI value of the living creatures in the army |
| `growth/2` | over all the player's towns and built dwellings: AI value times half the weekly growth |
| `alliance` | 5% of the AI value of the eligible creatures in all the player's heroes and towns, plus `T/5` |
| `ballista`, `tent` | own formulas: the Ballista from Attack and Artillery, the First Aid Tent from the most valuable creature in the army |

Notes on the table:

- One-stat weapons and shields are entered one point low: Centaur's Axe (+2 Attack) has `n = 1`, Sword of Hellfire (+6) has `n = 5`. Mixed items are entered at their net sum, for example Titan's Gladius (+12, −3) has `n = 9`.
- Thunder Helmet and Titan's Cuirass are entered as `+12, −3` although the items give `+10, −2`.
- An artifact with no entry is worth 0 by this table and gets only the floor of 10: the Spell Book, the Catapult, and anything not listed.
- Attack and defence are valued through the army, Spell Power and Knowledge through the hero's own spell values.

Combination artifacts have entries of their own; a part also receives the terms of its combination, as said above.

| ID | Combination | Terms |
|---|---|---|
| 129 | Angelic Alliance | `alliance` |
| 130 | Cloak of the Undead King | `necro 30` |
| 131 | Elixir of Life | `living/8` |
| 132 | Armor of the Damned | `T×15% + T×6/40 + Sh×10%` |
| 133 | Statue of Legion | `growth/2` |
| 134 | Power of the Dragon Father | `T×12/40 + 6×SP + 6×K + T×10%` |
| 135 | Titan's Thunder | `spell 57` |
| 136 | Admiral's Hat | `(T+2500)×12%` |
| 137 | Bow of the Sharpshooter | `Sh×7%` |
| 138 | Wizard's Well | `T×10% [W]` |
| 139 | Ring of the Magi | `50×D` |
| 140 | Cornucopia | `3×4×w(crystal) + 3×4×w(gems) + 3×4×w(mercury) + 3×4×w(sulfur)` |

### Wearing and replacing

`0x4339e0` is the value of **gaining** an artifact, and it is what every comparison uses:

- If the hero has a free slot the artifact fits, the gain is the artifact's full value, not below 0.
- If every fitting slot is taken, the gain is the new artifact's value minus the value of the artifact now worn there, not below 0. Worn artifacts are valued with a flag that keeps what the hero would lose by taking them off (see Recanter's Cloak above).

When a hero's total worth is summed (`0x433c60`), the terms for primary skill points are skipped, because the skills are already counted. **[code]**

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
| Prison (62) | 0 if the player already has eight heroes; otherwise the AI Value of the prisoner's army plus 2500 gold at the gold weight (`0x52a3a0`) |
| Buoy (11), Temple (96): morale | Not if already under its effect, and only if reachable with today's movement. `army strength × (sum of primary skills + 40) / 40 ×` the morale step value, the same 1.73% / 8.33% table as for [artifacts](#artifact-effect-terms). The Buoy is skipped by an all-undead army |
| Swan Pond (14), Faerie Ring (28), Fountain of Fortune (30), Mermaids (52): luck | The same with the luck step value (1.73% / 1.22%). The Swan Pond, which ends the hero's day, counts only when the hero would arrive with at most 200 movement points left, and the trip is then priced as costing all remaining movement |
| Idol of Fortune (38) | Luck or morale by the day of the week, both on day 7, valued as above |
| Fountain of Youth (31) | 10000 when it is less than 200 movement points away and the hero is not under its effect; otherwise a movement-bonus value with the distance shortened by 200 |
| Oasis (56), Watering Hole (110) | Movement-bonus routine `0x52a1e0` with 400 and 200 (not read further) |
| Library of Enlightenment (41) | 0 if visited or if `hero level + 2 × Diplomacy level` is below 10. Otherwise `army strength × 4 / 40 + 2 × (value of a Spell Power point + value of a Knowledge point)` |
| Mercenary Camp (51), Scholar (81) | Priced through experience: experience to the hero's next level × the hero's value of one experience point. The camp is 0 once visited |
| Redwood Observatory (58), Pillar of Fire (60) | Exploration value `0x432220`, the routine used for unexplored map |
| Hut of the Magi (37) | A value kept per player (`0x692950 + player × 0x98 + 4`): the sum of the exploration value (`0x432220`) at every Eye of the Magi (27) on the map (`0x429910`). Recomputed at most once per turn, after a hero's move, above Easy and only for a player with towns; set to 0 when that player visits a hut |
| Lean To (39), Windmill (112) | 3 and 4.5 times the player's **average resource value**: the sum of the weights of the non-gold resources divided by 5, computed at the end of the [resource weight](#what-resources-are-worth) routine. The multipliers match the average yield (1–5 and 3–6 units). The Lean To only if this player has not taken it, the Windmill only if it is not already its own and empty **[the summed terms are inferred]** |
| Water Wheel (109) | Another player's or unowned: 1000 gold at the gold weight. Own: `500 × weeks accumulated` gold at the gold weight |
| Shipwreck Survivor (86), Warrior's Tomb (108) | The player's [artifact-worth figure](#per-hero-and-per-player-figures), only while the hero carries fewer than 64 artifacts. The tomb is 0 once this player has visited it |
| Garrison (33) | Own garrison with removable troops: the [army gain](../ai-towns/#army-exchange-with-the-garrison) from it, and only from week 2 on some maps. Another player's that is not an ally: the [fight value](#valuing-a-fight) |
| School of Magic (47), School of War (107) | 0 if visited or the player has less than 1000 gold. School of Magic: the larger of the hero's Spell Power and Knowledge point values. School of War: priced through experience like the Mercenary Camp |
| Magic Spring (48) | Only when it has water: the hero's stored value of a double mana refill, with the same distance rule as the Magic Well |
| Rally Flag (64) | Not if already under its effect: morale and luck step values together, and the trip is priced 200 movement points shorter for the movement it gives back |
| Stables (94) | If not visited this week: 10000 when the Stables are nearer than half of the movement they would add over the rest of the week, otherwise 50 with the trip priced shorter by that amount. Plus, for Cavaliers in the army, `(AI Value of a Champion − AI Value of a Cavalier) × their number` for the free upgrade |
| Refugee Camp (78) | The [army gain](../ai-towns/#the-gain-of-adding-a-stack) of what it offers that the player can pay for |
| War Machine Factory (106) | Sum over the three machines of the same test as for the [town Blacksmith](../ai-towns/#when-a-hero-visits-its-own-town): the machine's value to the hero if it lacks it and the player can pay |
| University (104) | 0 with eight skills or under 2000 gold. Otherwise the sum of the [level-up skill values](#level-up-choices) of the offered skills the hero lacks and would accept |
| Witch Hut (113) | If this player has not seen what it teaches: experience to the hero's next level × the hero's value of one experience point. Once known: the skill's level-up value if the hero has fewer than eight skills, lacks it and would accept it; otherwise 0 (`0x52b900`) |
| Tree of Knowledge (102) | 0 if visited. Value of the level through experience. If the player does not yet know what this tree asks for, a discount of up to two thirds; if it asks for gold, only with 2000 gold; if gems, only with 10 gems |
| Seer's Hut (83) | Not yet visited by this player: the reward value, at least 20. Visited: reward value minus the value of what must be handed over, and only if the hero can complete the quest now and the deadline has not passed; otherwise 0 |
| Crypt (84), Shipwreck (85) | 0 once cleared. Otherwise the [fight value](#valuing-a-fight) against the guards with the reward counted at the resource weights, as for creature banks |
| Spell Scroll (93) | 0 with 64 artifacts. Otherwise 10, plus the fight against its guards if any, plus the value of the spell if the hero does not know it |
| Sea Chest (82), Wagon (105) | Sea Chest: 1200 gold at the gold weight plus one tenth of the artifact-worth figure; only the gold part when the hero carries 64 artifacts (`0x52a870`). Wagon: 0 once this player has visited it; otherwise `1.75 × average resource value + 0.4 × artifact-worth figure` (`0x52b710`) |
| Sirens (92) | Weighs the two effects against each other: the experience gained for the creatures given up, at the hero's value of an experience point, minus the strength of the 30% of each stack that is lost. A hero with no use for experience sees only the loss |
| Keymaster's Tent (10) | 5000 if this player has not visited that colour, otherwise 0 |
| Campfire (12) | For `n` units of its resource: `100 × n` gold at the gold weight plus `n` at that resource's weight |
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

Towns and heroes are covered in the next section. Teleporters are path edges, see [monoliths, gates and whirlpools](#monoliths-gates-and-whirlpools). Every case of the object switch is now listed.

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

A town whose garrison was saved by the emergency purchase is not marked.

The same routine tags the **enemy hero**: it stores `5,000,000 / number of the computer player's towns` in that hero's record. This is the "term for the hero itself" below. **[code]**

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
- If one is an upgrade and the other is new (`0x524dd0`): the routine ranks, by the same value, every skill the hero does not have and its class can learn, together with the one on offer. The hero has `8 − skills known` free slots; the new skill is taken only if it ranks within that many places from the top. Otherwise the hero takes the upgrade.

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
