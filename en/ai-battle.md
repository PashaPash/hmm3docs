---
title: "AI: battle"
parent: English
nav_order: 12
lang: en
---

# AI: battle
{: .no_toc }

How a computer-controlled side picks an action for each stack. The same code drives AI heroes, hero-less armies (see [neutral monsters](../ai-neutral/)) and a human player's auto-combat.

1. TOC
{:toc}

## Summary

- Every candidate action is scored in one currency: **Fight Value** of the units expected to die, adjusted by attack and defence. The AI maximises "value I destroy minus value I lose".
- The **game difficulty** switches whole parts of the logic on and off. Easy uses the bare scoring. Normal adds threat awareness. Hard and above add waiting, anti-clumping and escaping. There is no further change between Hard, Expert and Impossible in these routines, apart from the retreat threshold.
- A human player's auto-combat always runs with everything enabled, regardless of difficulty.
- The AI never surrenders. It only retreats, and only with a hero.

## Turn flow

| Step | Function | What happens |
|---|---|---|
| 1 | `0x477ee0` | AI turn for the active side. Outside the tactics phase it first asks "should I flee?" (`0x41e570`). |
| 2 | `0x4221f0` | Otherwise choose an action for the active stack. Default is Defend. |
| 3a | `0x41f060` | Stack can shoot right now, or is a Ballista: shooter logic. |
| 3b | `0x421f80` → `0x421680` | Everything else: melee logic. |
| 4 | `0x421280` | Creature spellcasters may cast instead. |
| 5 | `0x421f80` tail | Nothing useful found: Wait or Defend. |

"Can shoot right now" (`0x4428f0`) means: has the shooter flag, has shots left, and no enemy stands next to it. The adjacency check is skipped when the hero wears artifact 137 (Bow of the Sharpshooter). Ballista and Arrow Towers always count as shooting. **[code]**

The chosen action is written to the combat manager as an action code: 2 walk, 3 defend, 4 retreat, 5 surrender, 6 walk and attack, 7 shoot, 8 wait, 10 creature spell, 12 skip. **[code `0x421680`, `0x4222c0`, `0x41f060`]**

## What a unit is worth

`0x442a50` returns the value of **one unit** of a stack:

```
unit value = Fight Value × sqrt(attack factor × defence factor)

attack factor  = 1 + 0.05 × (attack  − creature's base attack  − baseline)
defence factor = 1 + 0.05 × (defence − creature's base defence − baseline)
```

- `Fight Value` is the column from [the creature table](../creatures/).
- "attack" and "defence" are the stack's current values in this battle, so they include the hero's primary skills and active spells.
- The **baseline** is the smallest such bonus found among all stacks on the field (`0x435ec0`). The side with the better hero therefore has every unit valued higher.
- Modifiers to the attack factor: ×0.5 for a shooter that cannot shoot at the moment; ×2 for a creature with the double-shot flag when it shoots; Bless and Curse scale it by maximum or minimum damage relative to average damage; a Ballista is multiplied by 1 / 1.5 / 1.5 / 2 for the hero's Artillery level (none / basic / advanced / expert) and doubled again from Advanced. **[code; table at `0x63b7f0`]**
- Modifiers to the defence factor: Shield (against melee) or Air Shield (against shots) by the spell's stored factor; ×0.5 when petrified; a per-hero factor from `0x4e4310` that is not decoded yet.
- Summoned stacks and war machines are scaled down by `HP of the rest of the army / (own HP + HP of the rest)`.
- The square root is **[inferred]**: `0x617b94` is a C runtime math wrapper and the same expression shape is used for hero strength.

`0x442fd0` converts **damage** into value: `unit value × damage / hit points per unit`, counting the wounds already on the top unit when the hit finishes it. A clone is worth `count × unit value / 5`. **[code; constants `0x63ac48`…`0x63ac70`]**

### Outnumbered mode

When the AI's side is worth less than half of the enemy (`own total × 2 < enemy total`) and the difficulty is Normal or higher, the per-unit value is replaced by a flat **1000 for every creature**. The AI then goes for whatever kills the largest number of units, without caring which creature they are. **[code `0x435ec0`, `0x442fd0`]**

## Value of an attack

`0x435b90`, for attacker A and target T:

```
attack value = value(damage A deals to T) − value(damage T's retaliation deals to A)
```

Damage and retaliation come from a simulated exchange (`0x4359b0`) using the normal damage routine. Within one planning pass, damage already assigned to a target by other stacks is subtracted first, so the AI does not count the same kill twice.

## Melee stacks

`0x421680`. The stack builds a score for each of the 187 battlefield hexes, then scores each enemy stack.

### Hex scores

All start at 0 and only go down.

| Applies | Penalty | Code |
|---|---|---|
| always | Standing in a damaging obstacle: value of the damage it would take | `0x4214f0` |
| always, when a per-game flag at game `+0x1f698` is above 1 | Moat hexes during a siege: value of the moat damage. Moat damage by town type, in the executable: Castle 70, Rampart 70, Tower 150, Inferno 90, Necropolis 70, Dungeon 90, Stronghold 70, Fortress 90, Conflux 70 | `0x421590`, table `0x63bd18` |
| Normal+ | Hexes that an enemy melee stack can reach this turn, if that stack is not already able to hit one of ours: value of the damage it would deal to this stack | `0x420260` |
| Hard+ | Hexes next to friendly stacks, when the enemy has breath attackers, area shooters, or a hero who can afford an area spell (Frost Ring, Fireball, Inferno, Meteor Shower): value of the expected splash damage | `0x41fb60`, `0x41f920` |

Penalties are capped at the full value of the stack itself.

### Scoring a target

For each living enemy stack except Arrow Towers:

1. Find the best hex to attack from (`0x436840`, `0x436300`). Fewer turns to get there wins, then the higher hex score, then the shorter path. On Normal+ a hex also gains value for extra enemies hit by a breath or all-around attack and loses value for exposure to the same from the target. Cavaliers and Champions (ids 10, 11) prefer the **longer** path on Normal+, which is the jousting bonus.
2. `score = attack value + hex score`. On Hard+ a bonus is added when other friendly stacks are already going to hit the same target and absorb its retaliation (`0x41f3b0`).
3. The score is multiplied by a random percentage and divided by the number of turns needed to reach the target. The range of the random factor is not recovered yet.
4. On Normal+ an attack with a negative score is dropped. Harpies and Harpy Hags (72, 73) ignore the hex penalty because they fly back.

The best target is chosen in this order: a target that is not blinded, petrified or paralysed beats one that is; fewer turns to reach; higher score. **[code `0x421680`]**

### What the stack then does

| Situation | Action |
|---|---|
| Best target reachable this turn | Walk and attack from the chosen hex |
| Best target further away | Move towards it (`0x41f580`). On Hard+, if stepping closer does not improve the hex score, **Wait** instead |
| No worthwhile target | Try a creature spell; then try to stand next to a friendly shooter that needs cover (`0x420760`); on Hard+, if the current hex has a negative score, move to the best reachable hex (`0x4208f0`) |
| Attacker in a siege with nothing to hit | Walk towards the wall line (row limits table `0x63bd00`) |
| Nothing at all | **Wait** on Hard+ (if waiting is still possible this round), otherwise **Defend** (`0x421f80`) |

A stack under Bind, or with speed 0, does not move.

## Shooters

`0x41f060`, `0x41eb80`, `0x435cb0`. For each enemy stack:

```
shot value = attack value computed with ranged damage
```

On Easy the largest shot value wins. On Normal+ it is divided first:

| Target | Divisor |
|---|---|
| Blinded, petrified or paralysed | 10 |
| Able to act and already has a victim picked in the threat pass | turns it needs to reach that victim, if fewer than 6 **[inferred from `0x448bd0`]** |
| Anything else | 5 |

So an AI shooter prefers the enemy stack that will hit its army soonest, and mostly ignores disabled stacks. Among equal candidates an active target beats a disabled one.

- Magogs (45), Liches (64) and Power Liches (65) score an aim hex by area effect instead (`0x41eda0`).
- Creatures with the wall-breaking flag may shoot walls during a siege (`0x41eea0`).
- No valid target: Defend.
- In the tactics phase a shooter moves to the allowed hex with the fewest empty neighbouring hexes and never next to another shooter stack; on Easy it does not reposition (`0x422060`).

## Creature spellcasters

`0x421280`. Allowed when it is not the tactics phase, magic is not blocked on this battlefield, neither hero wears artifact 126 (Orb of Inhibition), and the stack has charges left.

| Creature | Routine | Choice |
|---|---|---|
| Archangel (13), Pit Lord (51) | `0x421000` | Resurrection / raising demons from a dead stack |
| Master Genie (37), Ogre Mage (91) | `0x420d20` | The friendly stack with the highest benefit score (`0x43c4a0` for genies, `0x43c330` for ogre magi); war machines excluded |
| Faerie Dragon (134) | `0x420f00` | The hex with the highest score from `0x43c620`, over all hexes except the two edge columns |

## Berserk and similar states

`0x4456d0`: a stack that does not obey its owner picks a **random** target from the list of stacks it may attack. Shooters shoot it, others walk to it and attack.

## Retreat

`0x41e570`, called before the stack action.

Never considered when:

- the side has no hero;
- difficulty is Easy; on Normal a random roll skips the check part of the time **[inferred: about half]**;
- either hero wears artifact 125 (Shackles of War);
- the hero is the one named in a "lose this hero" condition;
- the player has no suitable town left to return to **[inferred from a building-mask test on the player's towns]**.

Immediate retreat: the AI is attacking a castle-level fortification, has no flyers, no shooters, the walls are intact and every defender is behind them (`0x41e440`).

Otherwise the hero must be worth saving: total artifact value at least 1000 or experience at least 2000. Then:

```
share = own strength / (own strength + enemy strength)      strength = Σ count × Fight Value

threshold = base + bonus − (4 − difficulty) × 0.015 − (0.06 if attacker)
  base  = 0.16 with no artifact value, 0.20 up to 5000, 0.21 up to 10000, 0.22 above
  bonus = experience / 200000, at most 0.03
  if threshold > 0.16 then threshold = 0.16

retreat when share < threshold
```

Difficulty is 0 for Easy to 4 for Impossible. A Normal-difficulty defender with some artifacts retreats below about 15.5% of the total strength, an attacker below about 9.5%.

The check also compares the player's gold with a surrender-style cost plus 2500; that part is not fully decoded.

**Surrender**: the branch that sets action 5 runs only for a human-owned side (auto-combat) after a confirmation dialog. For a computer player the same function always ends in action 4, retreat. **[code `0x477ee0`]**

## Hero spells

Entry `0x422da0`: the hero has not cast this round, it is not the tactics phase, magic is not blocked, the hero has a spell book, and nobody wears the Orb of Inhibition. The spell choice itself (`0x43c800` and the evaluator class at vtable `0x63b7d8`) is not decoded yet.

## What difficulty changes

For a computer-controlled side. "Human auto-combat" always behaves like the last column.

| Behaviour | Easy | Normal | Hard and above |
|---|---|---|---|
| Retreat | never | sometimes checked | checked |
| Outnumbered mode (flat unit value) | no | yes | yes |
| Avoid hexes enemy melee can reach | no | yes | yes |
| Count extra targets for breath / all-around attacks | no | yes | yes |
| Jousting path for Cavaliers | no | yes | yes |
| Shooters weigh targets by how soon they arrive | no | yes | yes |
| Drop attacks with negative value | no | yes | yes |
| Reposition shooters in tactics phase | no | yes | yes |
| Avoid clumping against area damage | no | no | yes |
| Use Wait | no | no | yes |
| Leave a dangerous hex when idle | no | no | yes |
| Credit for shared retaliation | no | no | yes |
