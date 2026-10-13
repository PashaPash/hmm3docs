---
title: Combat rules
parent: English
nav_order: 5
lang: en
---

# Combat rules
{: .no_toc }

Damage, morale, luck, turn order and retaliation. Siege rules are partly covered.

1. TOC
{:toc}

## Damage

Creature stats are in the [creature table](../creatures/) (HotA changes: [list](../hota/#creatures)). How the computer uses this formula to pick targets is in [AI: battle](../ai-battle/#value-of-an-attack).

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
| Attacking hero's Offence (melee) or Archery (ranged), Bless specialist | See [hero skills](#hero-skills-in-the-formula) |

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

The defending hero's Armorer factor is applied last. Shield and Air Shield are applied as stored per-stack factors.

### Hero skills in the formula

`0x4e42b0`, `0x4e4160`, `0x4e4310`, `0x4e5ff0`. Tables at `0x63e9f8`, `0x63e9e8`, `0x63ea08`.

| Skill | Basic | Advanced | Expert | Where it goes |
|---|---|---|---|---|
| Offence (melee attacks) | 10% | 20% | 30% | added to the bonus sum |
| Archery (ranged attacks) | 10% | 25% | 50% | added to the bonus sum |
| Armorer (damage taken) | 5% | 10% | 15% | final multiplier `1 − value` |

- A hero whose specialty is that skill multiplies the value by `1 + 0.05 × hero level`. Armorer cannot exceed 100%.
- The three bow artifacts add 5%, 10% and 15% to the Archery value, also when they are part of an assembled combination. They are counted **only if the hero has the Archery skill**; without it they add nothing to damage.
- A Bless specialist adds `3% × (hero level / creature level, rounded down)` of base damage to a blessed stack, where creature level is 1 to 7.

Because Offence and Archery are terms of the sum, they do not multiply the attack-skill bonus: Expert Offence on top of +100% from Attack gives +130%, not +160%.

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

### Arrow Towers and war machines

Battle setup around `0x4521f0`; tower strength from `0x5bf4f0`.

| Fortification | Towers |
|---|---|
| Fort | none |
| Citadel | the central keep |
| Castle | the keep and two side towers |

- A tower is an "Arrow Tower" stack: attack 10, damage 2–4 per shooter, and it goes through the normal damage formula.
- The keep has `4 + number of qualifying buildings built in the town` shooters. Each side tower has half of that, rounded up. Which buildings qualify is a per-town mask that was not decoded; **[inferred]** to be the town's own building set.
- The defender in a siege does not get a Ballista on the battlefield, even if the hero owns one. First Aid Tent and Ammo Cart are placed as usual.

### Catapult shots

`0x445d30` (one firing), `0x445ec0` (one shot), section table `0x63be60`.

The walls are eight targets: the upper tower, two wall sections, the gate, two more wall sections, the lower tower and the keep. A target can be shot at while it still has structure points. The two side towers count only when the town has a Castle, the keep only from a Citadel up (`0x476440`).

The row of the table above is chosen by the Ballistics level of the Catapult's hero. Cyclopes and Cyclops Kings throw with the Basic and Advanced rows whatever the hero knows.

For each shot of the firing:

1. **Damage** is rolled first, `rand(1,100)` against the three damage chances of the row: no damage, 1 point or 2 points.
2. **Hit roll**: `rand(1,100)` against the chance for the kind of target aimed at (keep, tower, gate or wall).
3. **A miss is not wasted.** It lands on another **wall section** that is still standing: the one nearest in order along the wall to the aimed target, a coin flip between two equally near ones. Only if no wall section stands is the shot lost.
4. If more shots remain and the aimed target has just been destroyed, the aim moves to the nearest target still standing, again with a coin flip for ties. When nothing is left to shoot at, the firing ends.

So a Catapult aimed at the keep with no Ballistics hits it 5% of the time, and nearly all the other shots chip at the walls instead. **[code and assembly; "nearest" is by index in the section list]**

Where the first aim comes from: a human picks the target. For a computer-controlled Cyclops, `0x41eea0` aims at a wall only for the attacker, only while enough of its army has no victim it can reach, and then picks the standing wall section with the **fewest structure points left**, at random among equals. The automatic aim of the Catapult itself (`0x473c00`, `0x476bd0`) was not read.

Not decoded: how an Arrow Tower picks its target, and the gate and drawbridge rules.

