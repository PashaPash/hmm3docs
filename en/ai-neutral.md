---
title: "AI: neutral monsters"
parent: English
nav_order: 13
lang: en
---

# AI: neutral monsters (armies without a hero)
{: .no_toc }

Wandering stacks, and any other army that fights with no hero on its side.

1. TOC
{:toc}

## Before the fight: join, flee or fight

`0x4a7740` runs when a hero steps onto a wandering stack.

### Inputs

| Symbol | Meaning | Source |
|---|---|---|
| `A` | Aggression of this stack, a small signed number stored with the stack on the map (bits 12–16 of its data word; the stack size is bits 0–11) | **[code]** |
| `R` | `hero army strength / (AI Value of the creature × stack size)` | **[code]** |
| `C` | Sympathy, 0 to 2 | `0x4a75c0` |
| `D` | Hero's Diplomacy level, 0 to 3 | hero skill byte |

Hero army strength (`0x427650`):

```
Σ (AI Value × count) over the hero's seven slots  ×  sqrt((1 + 0.05 × Attack) × (1 + 0.05 × Defence))
```

Attack and Defence are the hero's primary skills, each clamped to 0–99. **[code `0x44ac80`, `0x4e5400`]**

Power factor `P` from `R`:

| R | P |
|---|---|
| 7 or more | 11 |
| 1 up to 7 | `trunc(2 × R − 2)`, so 0 at equal strength, 2 at double, 6 at four times |
| above 0.5, below 1 | −1 |
| above 0.333, up to 0.5 | −2 |
| 0.333 or less | −3 |

Sympathy `C`: count the units in the hero's army that are the same creature as the stack or its upgraded/base counterpart.

- none: 0
- some: 1
- more than half of all units in the army: 2

On **Easy**, a human player's Diplomacy is treated as one level higher, up to 3. **[code: difficulty byte equals 0 and the interactive flag is set]**

### Decision

```
total = P + C + D

if total < A:                      fight
else if C + D + 1 >= A:            offer to join for free
else if A <= C + 2×D + 1 and the player has the gold:
                                   offer to join for gold
if nobody joined:
    if total == A or the stack is flagged "never flees":   fight
    else:                                                  the stack flees (the player may pursue)
```

- Price for a paid join: `creature gold cost × stack size`. **[code `0x4a7250`]**
- Without Diplomacy and without sympathy (`C = D = 0`), a free join needs `A ≤ 1`. Army strength does not help to recruit, it only decides between fight and flee.
- Each Diplomacy level raises the free-join limit by 1 and the paid-join limit by 2.
- If the player declines an offer, the stack then flees or fights by the same last rule.

How the map's disposition setting (compliant … savage) turns into `A` when the map is loaded is not traced yet.

## How the stack is split for battle

`0x4ac580` builds the defending army when a fight starts.

1. The random generator is **seeded from the stack's map coordinates** before anything is rolled. The same stack on the same tile therefore splits the same way every time; reloading does not change it. **[code; the seeding call `0x50c5f0` is inferred to be `srand`]**
2. `ratio = AI Value of the hero's army / AI Value of the monster stack` (plain `Σ AI Value × count`). **[code; two more calls on the hero precede the division and their effect on the ratio is not confirmed]**
3. Base number of stacks from the ratio (thresholds at `0x6776e0`):

   | ratio | stacks |
   |---|---|
   | below 0.5 | 7 |
   | 0.5 to 0.67 | 6 |
   | 0.67 to 1.0 | 5 |
   | 1.0 to 1.5 | 4 |
   | 1.5 to 2.0 | 3 |
   | 2.0 and above | 2 |

   The table also holds 3.0, but the loop stops before comparing it.
4. One roll of 1–100: on 1–20 one stack fewer, on 80–100 one stack more (never above 7).
5. The result is limited to at least 1 and at most the number of creatures.
6. Creatures are divided evenly; the remainder goes one each to the first stacks.
7. **Upgraded stack**: if the creature has an upgrade and there are at least 2 stacks, a second roll of 1–100 below 51 (50%) turns the **middle** stack (index `stacks / 2`) into the upgraded creature. The four basic elementals are excluded in games where the field at `+0x1f698` is 0.

The stronger the visiting army, the fewer and larger the neutral stacks. A weak hero meets up to seven small stacks.

## In battle

The combat rules these stacks fight under are in [Combat rules](../combat/); note that a hero-less side gets [no lucky strikes](../combat/#luck) and escapes a quarter of its [bad-morale freezes](../combat/#morale). Battles in which no human takes part are not fought on the field at all, see [battles without a battlefield](../ai-battle/#battles-without-a-battlefield).

A hero-less side runs exactly the same stack routines as an AI hero's army, described in [AI: battle](../ai-battle/). What differs follows from the missing hero:

| Topic | Hero-less side | Code |
|---|---|---|
| Retreat, surrender | Never. The first test in the retreat routine is "does this side have a hero" | `0x41e570` |
| Hero spells | None. The casting entry requires a hero | `0x422da0` |
| Creature spells | Yes: Master Genies, Ogre Magi, Faerie Dragons, Archangels and Pit Lords cast by the same rules | `0x421280` |
| Unit valuation | No hero attack/defence, so the neutral stack's own units sit at the baseline while the player's units are valued higher by the player's hero skills | `0x442a50`, `0x435ec0` |

### Difficulty applies to neutrals

The feature switches in the battle AI test the **game difficulty**, not who owns the army. A neutral stack is a non-human side, so:

- On **Easy**, neutral stacks use the bare logic: no threat avoidance, no waiting, shooters fire at whatever gives the largest immediate value, attacks with negative value are still made.
- On **Normal**, they avoid hexes your melee stacks can reach, shooters prefer the stack that will arrive first, and outnumbered stacks switch to flat unit values.
- On **Hard and above**, they also wait, spread out against area damage and breath attacks, and step out of dangerous hexes.

### Rules that follow for the player

All from the code paths above:

- **Neutral shooters** (Normal+) divide a target's value by the turns it needs to reach them, or by 5 when it has no victim in range. A fast stack that can reach them next turn draws fire ahead of a slow, more valuable one. A blinded, petrified or paralysed stack is divided by 10 and is almost never shot.
- **Neutral melee stacks** chase the target with the best `(damage value − retaliation value) / turns to reach`. A single cheap unit standing close has a tiny damage value, so it is not a strong lure by itself; what makes a target attractive is being close and losing a lot of Fight Value to the hit.
- **Outnumbered neutrals** (worth less than half of your army, Normal+) value every unit at a flat 1000 and therefore aim at the stack where they kill the most units, which favours your low hit point creatures.
- On Hard+ a neutral stack that cannot reach anything this turn will **wait** rather than walk into the range of your melee stacks.

## Creature banks

### When the contents are decided

Each bank's guards and reward are rolled **once, when the map is set up** (`0x47ad90`, called from the map object initialiser `0x4c0cc0`), and stored in a per-bank record. Visiting does not re-roll anything. **[code]**

1. **Level.** One roll of 1–100 is compared against the cumulative `Chance` column of `CRBANKS.TXT` for levels 1 to 3; if none matches, level 4.
2. **Reward.** Resources and reward creatures are copied from that row. Artifacts are picked at random per class, as many of each class as the row says.
3. **Guard stacks.** The row's guards are split by how many different creature types it has:

   | Guard types in the row | Stacks | Slot order | Slot that may be upgraded |
   |---|---|---|---|
   | 1 | 5 near-equal stacks | A A A A A | the third |
   | 2 | first type in 3 stacks, second in 2 | A B B A A | the fourth (type A) |
   | 3 | first and second type in 2 stacks each, third in 1 | A B C B A | the first (type A) |
   | 4 | not split | A B C D | the first |

   Splitting is by repeated integer division (`n / 5`, then the rest `/ 4`, and so on), so the stacks differ by at most one creature.
4. **Upgrade.** One roll of 1–100; if it is not above the row's `Upgrade` percentage and the creature has an upgrade, the whole stack in the marked slot becomes the upgraded creature. So at most one of the guard stacks is upgraded.

### The fight

`0x4abdc0`. The battle is started with the bank flag set and a random seed computed from the bank's map coordinates, so a given bank plays out from the same seed each time. The guards have no hero, so everything in [In battle](#in-battle) applies: no retreat, no hero spells, and the difficulty switches decide how cleverly they move.

A visited bank is marked per player (bits 5–12 of its data word) and marked empty (bit 25) once cleared. **[code `0x40d3f0`, `0x4a15a0`]**

### Table

From `CRBANKS.TXT` **[data]**.

> **HotA 1.8.1:** Naga Bank pays gems instead of sulfur and Dragon Fly Hive guards are never upgraded ([details](../hota/#creature-banks)); twelve banks are added, with guards listed stack by stack ([new creature banks](../hota/#new-creature-banks)). How the computer values a bank as a target is under [object values](../ai-adventure/#object-values-that-are-readable).

{% include banks.html lang="en" %}

## Growth and new stacks

### Weekly growth

`0x4c8780`, the new-week routine. For every wandering stack on the map that does not have the "does not grow" flag (bit 18 of its data word):

```
v = count × 16 + fraction          fraction is 4 bits kept with the stack (bits 27–30)
v = v + v / 10                     integer division
if v > 64000 then v = 64000
count = v / 16,  fraction = v mod 16
```

- Growth is 10% per week, compounded, with the remainder carried in sixteenths. A stack of 5 becomes 5 and 8/16, then 6 and 1/16, and so on; small stacks do grow, just not every week.
- The cap is 4000 creatures.

### Size of a random stack

When the map is set up, a wandering stack whose count is 0 gets a random count (`0x4c0cc0`). The bounds are passed in registers and were not read; they are **[inferred]** to be the "Adv. Map Low/High" columns of `CRTRAITS.TXT`, shown as "Map stack" in the [creature table](../creatures/).

> **HotA 1.8.1:** the size ranges of random stacks differ for about a dozen creatures, and AI Value differs for some, which shifts the join/flee ratio and the stack split; see [HotA differences: creatures](../hota/#creatures).

### New month

`0x4c8f40`. One roll of 1–10 at the start of each month:

| Roll | Month |
|---|---|
| 1–5 | ordinary |
| 6–9 | month of a creature: town growth of that creature doubles, and new wandering stacks of it appear |
| 10 | plague: creatures available in towns are halved |

In a creature month every free, eligible map tile has a 1 in 200 chance of getting a new stack of that creature, with a random aggression of 1–10. **[code; the lower bound of the month roll and the stack size bounds were not read]**

## Not decoded yet

- Where the split stacks are placed on the battlefield.
- Quick combat resolution for hero-less sides.
