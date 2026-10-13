---
title: "AI: battle"
parent: English
nav_order: 12
lang: en
---

# AI: battle
{: .no_toc }

How a computer-controlled side picks an action for each stack. The same code drives AI heroes, hero-less armies (see [neutral monsters](../ai-neutral/)) and a human player's auto-combat. It runs only when a human is in the battle; battles between computer players and neutrals are [resolved by a simulator](#battles-without-a-battlefield).

1. TOC
{:toc}

## Summary

- Every candidate action is scored in one currency: **Fight Value** of the units expected to die, adjusted by attack and defence. The AI maximises "value I destroy minus value I lose".
- The **game difficulty** switches whole parts of the logic on and off. Easy uses the bare scoring. Normal adds threat awareness. Hard and above add waiting, anti-clumping and escaping. There is no further change between Hard, Expert and Impossible in these routines, apart from the retreat threshold.
- A human player's auto-combat always runs with everything enabled, regardless of difficulty.
- The AI never surrenders. It only retreats, and only with a hero.
- An AI hero never casts Quicksand, Land Mine, Force Field, Fire Wall or Remove Obstacle.

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

- `Fight Value` is the column from [the creature table](../creatures/). HotA changes it for seven creatures ([list](../hota/#creatures)).
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

Damage and retaliation come from a simulated exchange (`0x4359b0`) using the normal [damage formula](../combat/#damage) and [retaliation rules](../combat/#retaliation). Within one planning pass, damage already assigned to a target by other stacks is subtracted first, so the AI does not count the same kill twice.

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
3. The score is multiplied by a random 75 to 100 percent and divided by the number of turns needed to reach the target. **[code: `rand(75,100)` at `0x421b02`]**
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
| Master Genie (37), Ogre Mage (91) | `0x420d20` | The friendly stack with the highest benefit score (`0x43c4a0` for genies, `0x43c330` for ogre magi); war machines excluded. When the stack also has an attack available, it skips casting 30% of the time |
| Faerie Dragon (134) | `0x420f00` | The hex with the highest score from `0x43c620`, over all hexes except the two edge columns |

## Berserk and similar states

`0x4456d0`: a stack that does not obey its owner picks a **random** target from the list of stacks it may attack. Shooters shoot it, others walk to it and attack.

## Retreat

`0x41e570`, called before the stack action.

Never considered when:

- the side has no hero;
- difficulty is Easy; on Normal the check is skipped half of the time (`rand(1,100) < 51`);
- either hero wears artifact 125 (Shackles of War);
- the hero is the one named in a "lose this hero" condition;
- the player has no town with a **Tavern** to rehire the hero in (the test uses the Tavern's building mask, the same one the [hiring routine](../ai-adventure/#hiring-heroes) checks).

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

Entry `0x422da0`, chooser `0x43c800`. The AI hero casts at most one spell per round, before the active stack's action is chosen.

### Preconditions

Spell numbers are in the [spell table](../spells/); HotA changes a few of them ([list](../hota/#spells)).

The hero has not cast this round, it is not the tactics phase, magic is not blocked on this battlefield, the hero has a spell book, and neither hero wears artifact 126 (Orb of Inhibition). **[code `0x422da0`]**

### Candidate spells

Each of the 70 hero spells is a candidate when:

- the hero knows it and it is flagged as a combat spell;
- the hero has the mana for it (cost at the hero's school level, after battlefield and enemy modifiers);
- on battlefield type 2 only level 1 spells pass **[the type is not identified yet]**;
- if either hero wears artifact 83 (Recanter's Cloak), only level 1 and 2 spells pass.

### Scoring

```
score = evaluator value × mana factor × random(75…100)%

casts = floor(mana / cost)
mana factor = 2.5            if casts >= 7
            = sqrt(casts)    otherwise
```

A hero short on mana therefore needs a much better spell before spending it. The highest score wins. **[code `0x43c800`; square root inferred]**

The winning spell is cast only if its evaluator also marked it as **worth casting now** (see timing below).

### Evaluators

All values use the same currency as stack actions, [unit value](#what-a-unit-is-worth) of what is gained or destroyed.

| Spells | Routine | Value |
|---|---|---|
| Magic Arrow, Ice Bolt, Lightning Bolt, Implosion (15–18), Titan's Lightning Bolt (57) | `0x436f60` → `0x436e30` | Value of the damage on the best target. Damage comes from the real spell routine, so immunities and resistances count, and is capped at the stack's remaining hit points. If the target is blinded, petrified or paralysed and would survive, the value becomes `2 × value − full stack value`, normally negative, so the AI does not wake a disabled stack |
| Frost Ring, Fireball, Inferno, Meteor Shower (20–23) | `0x437040` | Tries every hex except the two edge columns. `E` = value destroyed on the enemy side, `O` = on its own side. Score `E − O`, but only if `E > O`, `E / enemy total > O / own total` and `O < own total` |
| Death Ripple, Destroy Undead, Armageddon (24–26) | `0x436fb0` | Same `E − O` rule over the whole field |
| Summon elementals (66–69) | `0x43bb20` | `AI Value of the elemental × number summoned` |
| Haste (53) | `0x439550` | Only for a stack that already has a victim. Gain = value of the exchange it gets if Haste lets it arrive this turn, plus `stack value × turns saved / planning horizon` |
| Slow (54) | `0x439270` | Only for an enemy stack that has a victim. Gain = the exchange it is prevented from making this turn, plus `stack value × extra turns / planning horizon`, scaled by the chance the spell takes effect |
| Blind (62), Paralyze-type (74) | `0x439100` | Only for enemy stacks that threaten the AI's army this turn; derived from the stack's full value |
| Bless (41) | `0x437430` | Only for a stack whose victim is reachable this turn; value of the extra kills from maximum damage |
| Shield (27), Air Shield (28) | `0x438c60`, `0x438bc0` | Uses the melee or ranged damage each friendly stack is expected to take this round (`0x43c040`) |
| Age (75) | `0x4373f0` | One third of the target's value |
| Chain Lightning (19) | `0x437310`, `0x437190` | Tries every legal enemy stack as the first target and follows the real chain: the number of jumps for the school level, damage halved at each jump, own stacks included. Then the same `E − O` rule as the area spells |
| Earthquake (14) | `0x43b8f0` | Attacker only, while walls still stand. Each own stack that has no victim yet adds its full value; each own shooter whose shot is blocked by the wall adds `value × wall sections the spell can break / (3 × sections standing)` |
| Resurrection (38), Animate Dead (39) | `0x43aca0` | For each own stack the spell is legal on: `unit value × creatures raised`, the number raised capped by the stack's losses. Considered only when the spell would not be wasted (it raises no more than was lost) or the stack has lost at least three quarters of its hit points |
| Sacrifice (40) | `0x43b1e0`, `0x43af50` | Every pair of a stack to raise and another own stack to give up. Value raised minus the full value of the stack given up, and only if that is positive |
| Teleport (63) | `0x43aa60` | Own non-shooters only: the stack's best attack score with a teleport minus its best score on foot, using the same [move scoring](#melee-stacks) |
| Dispel (35) | `0x43a910`, `0x439a80` | Runs over both sides. Every spell on a stack is re-valued with its own evaluator: removing a curse from an own stack or a buff from an enemy stack adds its value, removing an own buff or an enemy's curse subtracts it. Poison is left out |
| Cure (37) | `0x439c30` | The same sum over the harmful spells on the stack, plus the value of the hit points healed |
| Protection from Air, Fire, Water, Earth (30–33) | `0x4396e0` | Only when the enemy has a hero. Looks at the damage spells of that school the **enemy hero knows and can afford**, computes each one's damage on this stack, and values the protection at the damage it would prevent from the worst of them |
| Anti-Magic (34), Magic Mirror (36) | `0x439d40`, `0x439de0` | The same over all four schools. Anti-Magic counts spells up to the level it blocks and adds the Dispel value for the stack; Magic Mirror counts the share of damage its reflection chance removes |
| Fire Shield (29) | `0x43a110` | Only for a stack an enemy is expected to attack: value of the damage reflected back. Efreet Sultans, which have it already, count 20 points less |
| Bloodlust (43), Precision (44) | `0x438100`, `0x438b50` → `0x437800` | Bloodlust for melee stacks, Precision for shooters, and only when the stack's victim is reachable this turn: value of the extra kills from the attack bonus |
| Slayer (55) | `0x438d00` | The same, and only when the victim is one of the creature types the spell works against at the hero's level |
| Stone Skin (46) | `0x438910` | Value of the losses the defence bonus prevents this round |
| Prayer (48) | `0x438ac0` | Sum of the Stone Skin, Haste and (victim reachable this turn) Bloodlust values at Prayer's bonus |
| Frenzy (56) | `0x4375d0` | Victim reachable this turn: value of the extra kills from the attack gained |
| Counterstrike (58) | `0x439e80` | Only for a stack expected to be attacked more often than it can retaliate (Griffins count two retaliations, Royal Griffins are skipped): value of the extra retaliation damage |
| Clone (65) | `0x43b2e0` | Victim reachable this turn and the stack is not itself a clone: value of the damage the copy would deal |
| Mirth (49), Fortune (51) | `0x438170`, `0x438490` | Mirth: stack value times the morale step value of [0x435850](../ai-adventure/#artifact-effect-terms), 0 for creatures morale does not affect. Fortune: victim reachable this turn; extra damage times luck steps gained, divided by 24 |
| Curse (42), Weakness (45), Disrupting Ray (47), Sorrow (50), Misfortune (52) | `0x43b370`, `0x438ed0`, `0x438dc0`, `0x4382c0`, `0x438f60` | Only on enemy stacks that threaten the AI's army this turn. Value of the damage the stack loses (Curse, Weakness), of the defence it loses at 5% per point (Disrupting Ray), or the morale or luck step value (Sorrow, Misfortune), each scaled by the chance the spell takes effect |
| Forgetfulness (61) | `0x43b500` | Enemy shooters only: the difference between the stack's ranged and melee value |
| Berserk (59), Hypnotize (60) | `0x43a400`, `0x43a500` → `0x43a340` | Value of the damage the affected stack would do to another enemy stack: the average over the stacks hit for Berserk, the best victim for Hypnotize. Hypnotize skips stacks that are already blinded, paralysed or petrified |
| **Quicksand (10), Land Mine (11), Force Field (12), Fire Wall (13), Remove Obstacle (64)** | default `0x43b680` | Always 0. **The AI never casts these** |

For spells that hit one stack, the evaluator runs on every legal stack and keeps the best. When the hero's school level makes the spell a mass spell, the values of all affected stacks are added (`0x43a910`, `0x43a670`). Stacks already under the spell, disabled stacks, First Aid Tents and Ammo Carts are skipped. Against a target with Magic Mirror the value is multiplied by `(50 − mirror chance) × 2 / 100`.

Two things recur in these routines. A buff on a stack that attacks is worth something **only if that stack's victim can be reached this turn**; otherwise the value is 0 and the spell waits. And curses are considered only for enemy stacks **that threaten the AI's army this turn**, so the computer does not curse a stack that is still far away. The creature-only effects Poison (71) and Disease (73) have entries too but no hero can cast them.

Spell flag `0x200` is tested wherever the code needs "a spell that deals damage": here for the protections, in the parting shot, and in the [Orb artifacts](../ai-adventure/#artifact-effect-terms). **[inferred from use]**

### Timing

- A buff aimed at a friendly stack other than the active one is postponed while some other friendly stack still has to act this round, unless the spell carries spell flag `0x4000`. In practice the AI buffs the stack that is about to move. **[code `0x43a670`]**
- A spell on an enemy stack is cast at once when no other friendly stack is left to act, or when the active stack is about to attack that very target in melee this turn. Otherwise it is cast only if the target threatens the AI's army and no friendly stack that is still to act is faster than it. **[code `0x436c60`; reading of the last condition is inferred]**

### Parting shot

When the retreat check has already decided to flee, the chooser runs in a special mode: only spells with spell flag `0x200` are candidates, the timing test is ignored, and damage is valued at a flat 1000 per unit killed. The spell is chosen at the start of the stack's turn (`0x4782d0`), the retreat itself comes from the turn driver afterwards. **[code `0x422da0`, `0x43c800`; order inferred]**

## Battles without a battlefield

When no human-controlled side takes part, the game does not run the battle on the hex field at all. The battle start routine (`0x4ad470`) calls a simulator (`0x4270c0` → `0x426bc0`) and applies its result. **[code; that the two flags tested mean "this side is played by a human" is inferred]**

This is the same simulator the adventure-map AI uses to decide whether a fight is worth taking ([valuing a fight](../ai-adventure/#valuing-a-fight)). The two uses differ only in the strength multiplier given to each side:

| Use | Multiplier on each side's strength |
|---|---|
| AI planning | fixed: the hero's own factor, 1.25 for neutrals and computer opponents, a difficulty value for human opponents |
| Actual resolution | random: `rand(75,125) / 100` for the attacker, and a second independent roll for the defender **[range of the second roll inferred to be the same]** |

So the outcome the AI predicted and the outcome it gets are drawn from the same model, but the real one has up to ±25% luck on each side. A computer hero that attacked on a narrow predicted margin can lose.

### What the simulator does

`0x423ee0` and `0x424120` turn each army into a list of per-stack records and a pooled hit point total; `0x426bc0` then runs **at most three rounds**:

1. Decide for each side whether it shoots this round (`0x4267c0`).
2. Hero spells are applied by `0x425bd0`, first for the side whose fastest stack is faster.
3. Each side's damage for the round is computed (`0x426390`) and subtracted from the other side's pool; losses are then taken off the stacks in order (`0x426170`), rounding up the number of survivors.
4. Stop early if a pool reaches zero.

After the third round `0x4264d0` settles what is left. Hero Attack and Defence enter as 5% per point of difference between the two heroes, the same step as in the real [damage formula](../combat/#damage).

The attacker wins if its pool is still above zero. `0x426ee0` then writes the surviving counts back to the real armies.

### The arithmetic

**Strength points.** `0x424120` gives every stack a per-unit strength built from the creature's **Fight Value**, scaled by the hero terms (5% per point of Attack and Defence difference, and a square-root factor for bonus hit points from the hero) and by the side's multiplier from the table above. A stack's strength is `per-unit strength × count`, and a side's **pool** is the sum over its stacks. The pool plays the role of hit points: it is what the other side's damage is taken from.

**When a stack starts dealing damage.**

| Stack | First round it acts |
|---|---|
| Shooter | from the start, at range |
| Walker or flyer | round `(speed + 2 × (7 − Tactics advantage)) / speed`, integer division, at most 4 |
| Walker when attacking a town with walls | not before the wall delay stored for the siege; flyers ignore it |

"Tactics advantage" is the hero's Tactics level minus the opposing hero's, not below 0. A speed 5 walker with no Tactics arrives in round 3, a speed 9 one in round 2, a speed 15 one in round 1. Because the simulation is cut after three rounds, **slow walkers deal no damage before the settlement**.

**Damage per round** (`0x426390`). Every stack that is already acting removes from the enemy pool a fixed share of its own current strength:

| Situation | Share of the stack's strength per round |
|---|---|
| Melee | 20% |
| Shooter fighting in melee, without the "no melee penalty" flag | 10% |
| Shooter at range | 20%, or with a hero a value from the hero's ranged bonus divided by 5; doubled for double-shot creatures; halved when shooting at a walled town, except for Arch Magi |

Losses are then taken off the stacks in list order (`0x426170`): a stack loses whole units worth of the damage, and the survivor count is rounded up.

**Settlement after round three** (`0x4264d0`). The routine adds up each side's remaining fighting power. If both are above zero, the **weaker side is wiped out completely**, and the stronger side's pool is reduced by a final loss and its casualties distributed the same way. If that final loss empties the stronger pool too, both armies are destroyed.

So the model is: up to three rounds in which speed and shooting decide who gets free hits, then a winner-takes-all comparison of what is left.

Not read: the exact final-loss expression, the per-stack terms summed in the settlement, and how hero spells are picked and valued inside the simulator (`0x425bd0`). **[code]**


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
