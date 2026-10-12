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

## Not decoded yet

- Where the split stacks are placed on the battlefield.
- Creature bank guard layouts and the choice of level (the table itself is in `CRBANKS.TXT`).
- Weekly growth of wandering stacks.
- Quick combat resolution for hero-less sides.
