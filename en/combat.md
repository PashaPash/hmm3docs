---
title: Combat rules
parent: English
nav_order: 5
lang: en
---

# Combat rules
{: .no_toc }

Damage, morale, luck, turn order and retaliation. Siege rules are only partly covered.

1. TOC
{:toc}

## Damage

`0x443f40` computes the damage of one attack. `base` is the stack's rolled damage (per-creature roll times count; Bless and Curse replace the roll with the maximum or minimum).

```
damage = (base + bonus) × reduction × defending hero's factor        at least 1
```

### Bonus

`0x443320` and `0x443840`. Every item is a fraction of `base`, and the items are **added together**.

| Source | Bonus |
|---|---|
| Attack above the target's Defence | +5% per point, at most +300% |
| Lucky strike (see [Luck](#luck)) | +100% |
| Cavalier, Champion charging | +5% per hex travelled; none against Pikemen and Halberdiers |
| Opposed elementals: Air or Storm against Earth or Magma and the reverse; Fire or Energy against Water or Ice and the reverse | +100% |
| Hated enemy: Angels and Devils, Genies and Efreet, Titans and Black Dragons, each way, including upgrades | +50% |
| Dread Knight | 20% chance of +100% |
| Ballista | +100% with a chance by the hero's Artillery level: none 0%, Basic 50%, Advanced 75%, Expert 100% (table `0x63b810`) |
| Attacking hero's Offence (melee) or Archery (ranged), Bless specialist | Added here by `0x4e42b0` / `0x4e4160`; exact terms not read yet |

"Attack" and "Defence" are the stacks' current values: creature stats, hero primary skills and spell effects. Moat hexes lower the defender's Defence by 3 (`0x442590`).

### Reduction

`0x443b90`. These **multiply**.

| Condition | Factor |
|---|---|
| Target's Defence above the Attack | `1 − 0.025` per point, not below 0.3 |
| Ranged attack beyond full range | 0.5 |
| Ranged attack through walls | 0.5 |
| A shooter fighting in melee, unless it has the "no melee penalty" flag | 0.5 |
| Psychic Elemental attacking a creature immune to mind spells | 0.5 |
| Magic Elemental attacking a Magic Elemental or a Black Dragon | 0.5 |
| The attacker is retaliating while blinded or paralysed | the factor stored by that spell (see [Retaliation](#retaliation)) |

The defending hero's factor (`0x4e4310`, Armorer) is applied last; its exact form is not read yet. Shield and Air Shield are applied as stored per-stack factors.

### Two asymmetries worth noticing

- Attack advantage is worth 5% per point but Defence advantage only 2.5% per point.
- The attack bonus is capped at +300% (60 points of difference), the defence reduction at −70% (28 points).

**[code; constants at `0x63ac58`, `0x63ac28`, `0x63b8c0`, `0x63b8b8`, `0x63ac70`]**

## Morale

Checked when a stack's turn comes up. Morale is clamped to the range −3…+3 first.

| Roll | Function | Rule |
|---|---|---|
| Good morale | `0x464920` | After the stack has acted: `rand(1,24) <= morale` gives it another action. That is about 4.2% per point, 12.5% at +3. Not in the tactics phase, and not for a stack that is defending or already had its morale action |
| Bad morale | `0x464b40` | Before the stack acts: `rand(1,12) <= −morale` makes it lose the action. That is about 8.3% per point, 25% at −3 |

Two things are not symmetrical:

- A point of negative morale is twice as likely to trigger as a point of positive morale.
- When the stack's side is **not controlled by a human**, a triggered bad-morale roll is cancelled with a further 1 in 4 chance (`rand(1,4) == 1`). Computer and neutral stacks therefore freeze at three quarters of the human rate: 6.25% per point.

**[code]**

## Luck

`0x43f900` (melee) and `0x441610` (shooting), rolled for each attack.

- Luck is used only when it is positive and is capped at 3: `rand(1,24) <= luck`, about 4.2% per point, 12.5% at +3.
- A lucky strike adds +100% of base damage, as one more term in the bonus sum above.
- The roll is made **only if the stack's side has a hero**. A hero-less army, such as wandering monsters or bank guards, never gets a lucky strike.
- Negative luck does nothing in this executable.

**[code]**


## Turn order

`0x465080` picks the next stack; `0x464f50` compares two candidates.

A round has two passes. In the first, every stack that has not acted and has not chosen Wait is eligible. When none is left, the second pass runs over the stacks that waited.

Between two eligible stacks, the one that goes first is decided in this order:

1. A stack holding a good-morale extra action goes before any other.
2. Arrow Towers go before everything else, then the Catapult, then ordinary stacks.
3. **Speed**: higher first in the normal pass, **lower first in the waiting pass**.
4. Equal speed, different sides: the side that did **not** move last goes first, so ties alternate between the armies.
5. Equal speed, same side: the stack in the lower army slot.

Speed is the current value, so Haste and Slow change the order within the round. Ammo Carts never act.

When a stack is picked:

- If it is blinded, petrified or paralysed it is passed over.
- In the normal pass, [bad morale](#morale) is rolled; in the waiting pass and the tactics phase it is not.
- **Fear**: if the enemy army contains Azure Dragons, the stack loses its action with a 1 in 10 chance. Stacks with the "no morale" flag and Azure Dragons themselves are immune. `0x464d40`

**[code]**

## Retaliation

Each stack has a counter of retaliations, refilled at the start of the round:

| Stack | Retaliations per round |
|---|---|
| Most creatures | 1 |
| Griffin | 2 |
| Royal Griffin | unlimited (the counter is set to 5000) |
| Under Counterstrike | plus the number stored by the spell |
| War machines | 0 |

After a melee hit the target strikes back when all of these hold:

- it still has units alive;
- the attacker does not have the "no retaliation" flag;
- the target is not petrified;
- its counter is above 0.

The counter then drops by one. After the retaliation, a creature with the double-attack flag that is not shooting strikes a second time if the target still stands.

A **blinded or paralysed** target does retaliate, but its damage is multiplied by the factor the spell stored on it. These are the two spell-related entries in the [reduction](#reduction) table. **[code; the address of the melee routine is not pinned down yet]**

## Siege, partial

Only the pieces that came up while reading other code:

- Arrow Towers act first each round and the attacker's Catapult right after them (see turn order).
- A stack standing in the moat has 3 less Defence, and takes moat damage that depends on the town type: Castle 70, Rampart 70, Tower 150, Inferno 90, Necropolis 70, Dungeon 90, Stronghold 70, Fortress 90, Conflux 70 (table `0x63bd18`).
- Shooting through walls halves damage (see reduction).
- Catapult accuracy by the hero's Ballistics level, from `BALLIST.TXT` **[data]**:

{% include ballistics.html lang="en" %}

Not decoded: Arrow Tower damage, which wall section the Catapult aims at, gate and drawbridge rules.

