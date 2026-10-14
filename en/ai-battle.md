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
- Modifiers to the defence factor: Shield (against melee) or Air Shield (against shots) by the spell's stored factor; ×0.5 when petrified; the hero's [Armorer](../combat/#hero-skills-in-the-formula) factor `1 − value` (`0x4e4310`).
- Summoned stacks and war machines are scaled down by `HP of the rest of the army / (own HP + HP of the rest)`.
- The square root: `0x617b94` is the C runtime `sqrt` (sign check, then `fsqrt` at `0x617bbc`). **[assembly]**

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
| always, in Shadow of Death scenarios ([expansion level](../ai-overview/#expansion-level) 2) | Moat hexes during a siege: value of the moat damage. Moat damage by town type, in the executable: Castle 70, Rampart 70, Tower 150, Inferno 90, Necropolis 70, Dungeon 90, Stronghold 70, Fortress 90, Conflux 70 | `0x421590`, table `0x63bd18` |
| Normal+ | Hexes that an enemy melee stack can reach this turn, if that stack is not already able to hit one of ours: value of the damage it would deal to this stack | `0x420260` |
| Hard+ | Hexes next to friendly stacks, when the enemy has breath attackers, area shooters, or a hero who can afford an area spell (Frost Ring, Fireball, Inferno, Meteor Shower): value of the expected splash damage | `0x41fb60`, `0x41f920` |

Penalties are capped at the full value of the stack itself.

### Scoring a target

For each living enemy stack except Arrow Towers:

1. Find the best hex to attack from (`0x436840`, `0x436300`). Fewer turns to get there wins, then the higher hex score, then the shorter path. On Normal+ a hex also gains value for extra enemies hit by a breath or all-around attack and loses value for exposure to the same from the target. Cavaliers and Champions (ids 10, 11) prefer the **longer** path on Normal+, which is the jousting bonus.
2. `score = attack value + hex score`. On Hard+ a [bonus for drawing the retaliation](#bonus-for-drawing-the-retaliation) is added (`0x41f3b0`).
3. The score is multiplied by a random 75 to 100 percent and divided by the number of turns needed to reach the target. **[code: `rand(75,100)` at `0x421b02`]**
4. On Normal+ an attack with a negative score is dropped. Harpies and Harpy Hags (72, 73) ignore the hex penalty because they fly back.

The best target is chosen in this order: a target that is not blinded, petrified or paralysed beats one that is; fewer turns to reach; higher score. **[code `0x421680`]**

### Bonus for drawing the retaliation

`0x41f3b0`, added to a target's score in step 2. The active stack `A` gets credit for the attacks other friendly stacks can make on target `T` after `A` has taken its retaliation.

Conditions:

- Hard difficulty and above (or a per-side flag that was not identified);
- `A` can reach `T` this turn and is not blinded, petrified or paralysed;
- `T` is not petrified and has exactly one retaliation left;
- `A`'s attack does not kill `T`.

Let `R` be the hit points `T` has left after `A`'s attack. For every friendly stack `S` that can reach `T` this turn (arrow towers excluded):

```
follow-up(S) = value of the damage S would do to T, capped at R
gain(S)      = follow-up(S) − the value of the attack S has planned already

bonus = sum of positive gain(S) over stacks whose planned victim is T
      + the largest positive gain among the other stacks
```

The routine reads only the current state. It does not use which stack attacked which earlier, the order of turns, or whether `S` has already acted this round. The planned victim and planned attack value of `S` are the ones stored when `S` last chose a target. **[code and assembly `0x41f3b0`, call site in `0x421680`; "can reach this turn" is the reading of a per-stack bit mask and is inferred]**

> **HotA 1.8.1:** the same code, with one change found: every "out of action" test also counts a fourth, HotA-only effect, and Couatls have a special branch. See [HotA: battle AI code](../hota/#battle-ai-code).

### What the stack then does

| Situation | Action |
|---|---|
| Best target reachable this turn | Walk and attack from the chosen hex |
| Best target further away | Move towards it (`0x41f580`). On Hard+, if stepping closer does not improve the hex score, **Wait** instead |
| No worthwhile target | Try a creature spell; then try to stand next to a friendly shooter that needs cover (`0x420760`); on Hard+, if the current hex has a negative score, move to the best reachable hex (`0x4208f0`) |
| Attacker in a siege with nothing to hit | Walk towards the wall line (row limits table `0x63bd00`) |
| Nothing at all | **Wait** on Hard+ (if waiting is still possible this round), otherwise **Defend** (`0x421f80`) |

A stack under Bind, or with speed 0, does not move.

### Tactics phase

`0x4221f0`. During the tactics phase each of the AI's stacks gets one decision:

- **Shooters** (and stacks the routine treats like them) reposition as described under [Shooters](#shooters).
- **Everything else** runs the normal target choice above, but the attack branch and creature spells are switched off. The stack picks the target it would want and then **walks towards it** (`0x41f580`) as far as the tactics zone allows: hexes outside the zone are rejected, and the walk is not limited to one turn of movement. A stack with nothing to walk to stays where it is.

**[code]**

**When there is a tactics phase** (battle setup `0x462a20`): only when the two heroes' Tactics levels differ; the side with the higher level gets it.

**How the phase ends** (`0x475ed0`). The side's stacks act in turn; when all have acted, a new pass begins and they can act again. For a side under computer control (and in auto-combat) the phase ends at the end of a pass unless both hold:

- some stack moved or attacked during that pass (Defend and Wait do not count);
- fewer than three passes have been made.

So a computer side gets at most three passes over its stacks, and stops earlier once a pass changes nothing. **[code `0x475ed0`, `0x478d80`; the action numbers for Defend (3) and Wait (8) follow the battle action order]**


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

Among equal candidates an active target beats a disabled one.

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
- the side is a computer player and difficulty is Easy; on Normal the check is skipped half of the time (`rand(1,100) < 51`);
- either hero wears artifact 125 (Shackles of War);
- the hero is the one named in a "lose this hero" condition;
- the player has no town with a **Tavern** to rehire the hero in (the test uses the Tavern's building mask, the same one the [hiring routine](../ai-adventure/#hiring-heroes) checks);
- the hero defends the player's only Tavern town;
- the hero defends a besieged town, unless it is a Stronghold with the Escape Tunnel.

Immediate retreat (`0x41e440`): the AI is attacking a castle-level fortification, has no flyers, no shooters, the walls are intact and every defender is behind them.

Otherwise the hero must be worth saving. Its artifacts, worn and in the backpack, are summed, each at the larger of its [AI value](../artifacts/) (`0x433aa0`) and half its price. The sum must be at least 1000, or the hero's experience at least 2000. Then:

1. If no own stack can act (all are war machines or cannot move), retreat.
2. The check goes on only when the player has at least **the surrender cost plus 2500 gold** (`0x477a00`, the same cost the surrender branch uses).
3. Strengths are compared:

```
strength   = Σ count × Fight Value, × 1.2 for each stack that has not acted this round
             defender's strength × 1.1 in a siege
             the opponent's strength × 1.1 (always)
share      = own strength / (own strength + enemy strength)

threshold  = base + bonus − (4 − difficulty) × 0.015 − (0.06 if attacker)
  base  = 0.16 with no artifact value, 0.20 up to 5000, 0.21 up to 10000, 0.22 above
  bonus = 0.03 with at least 200,000 experience, otherwise 0
  if threshold > 0.16 then threshold = 0.16

retreat when share < threshold
```

Difficulty is 0 for Easy to 4 for Impossible. A Normal-difficulty defender with some artifacts retreats below 15.5% of the total strength, an attacker below 9.5%. **[code and assembly; constants `0x63abf8`…`0x63ac20`]**

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
- on special terrain 2 only level 1 spells pass. This is the Cursed Ground rule **[inferred from the rule itself; the same value is passed as the terrain to the school-level routine]**;
- if either hero wears artifact 83 (Recanter's Cloak), only level 1 and 2 spells pass.

### Scoring

```
score = evaluator value × mana factor × random(75…100)%

casts = floor(mana / cost)
mana factor = 2.5            if casts >= 7
            = sqrt(casts)    otherwise
```

The highest score wins. **[code `0x43c800`; square root inferred]**

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

A buff on a stack that attacks has a value only if that stack's victim can be reached this turn; otherwise it is 0. Curses are considered only for enemy stacks that threaten the AI's army this turn. Poison (71) and Disease (73) have entries but no hero can cast them.

Spell flag `0x200` is tested wherever the code needs "a spell that deals damage": here for the protections, in the parting shot, and in the [Orb artifacts](../ai-adventure/#artifact-effect-terms). **[inferred from use]**

### Timing

- A buff aimed at a friendly stack other than the active one is postponed while some other friendly stack still has to act this round, unless the spell carries spell flag `0x4000`. The flag is set, in the executable's spell table (`0x685450`, offset `+0xc`), on exactly the protective spells: Shield, Air Shield, Fire Shield, the four Protections, Anti-Magic, Magic Mirror, Stone Skin and Counterstrike. **[code `0x43a670`; data]**
- A spell on an enemy stack is cast at once when no other friendly stack is left to act, or when the active stack is about to attack that very target in melee this turn. Otherwise it is cast only if the target threatens the AI's army and no friendly stack that is still to act is faster than it. **[code `0x436c60`; reading of the last condition is inferred]**

### Parting shot

When the retreat check has already decided to flee, the chooser runs in a special mode: only spells with spell flag `0x200` are candidates, the timing test is ignored, and damage is valued at a flat 1000 per unit killed. The spell is chosen at the start of the stack's turn (`0x4782d0`), the retreat itself comes from the turn driver afterwards. **[code `0x422da0`, `0x43c800`; order inferred]**

## Quick combat

The **Quick Combat** option (registry value "Quick Combat", stored at `0x69877c`) does not use the simulator below. The battle is fought on the hex field as usual, but every stack of both sides is under computer control (`0x46a4a0`, `0x474bf0`), so the human's army is driven by the same [stack AI](#melee-stacks), [hero spell choice](#hero-spells) and [retreat check](#retreat) as a computer player's. In a hot-seat game between two humans it applies only when both players have it switched on. **[code]**

## Battles without a battlefield

When no human-controlled side takes part, the game does not run the battle on the hex field at all. The battle start routine (`0x4ad470`) calls a simulator (`0x4270c0` → `0x426bc0`) and applies its result. **[code; the test is the player's human flag, player record `+0xe2` (`0x4ce940`)]**

This is the same simulator the adventure-map AI uses to decide whether a fight is worth taking ([valuing a fight](../ai-adventure/#valuing-a-fight)). The two uses differ only in the strength multiplier given to each side:

| Use | Multiplier on each side's strength |
|---|---|
| AI planning | fixed: the hero's own factor, 1.25 for neutrals and computer opponents, a difficulty value for human opponents |
| Actual resolution | random: `rand(75,125) / 100` for the attacker, and a second independent roll for the defender **[range of the second roll inferred to be the same]** |

The predicted outcome and the real one come from the same model; the real one has a random ±25% on each side.

### What the simulator does

`0x423ee0` and `0x424120` turn each army into a list of per-stack records and a pooled hit point total; `0x426bc0` then runs **at most three rounds**:

1. Decide for each side whether it **closes to melee** this round (`0x4267c0`, see [order within a round](#order-within-a-round)).
2. Hero spells are applied by `0x425bd0`, first for the side whose fastest stack is faster; on a tie the attacker casts first.
3. Each side's damage for the round is computed (`0x426390`), both before either is applied, and then subtracted from the other side's pool and shared among its stacks (`0x426170`), rounding up the number of survivors.
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

The damage a side takes is shared among the eligible stacks **in proportion to their remaining pool points** (`0x426170`): each stack loses `damage × its pool / pool of all eligible stacks`, and its survivor count is rounded up. Which stacks are eligible is given under [order within a round](#order-within-a-round).

**Settlement after round three** (`0x4264d0`). The routine adds up each side's remaining fighting power. If both are above zero, the **weaker side is wiped out completely**, and the stronger side's pool is reduced by a final loss and its casualties distributed the same way. If that final loss empties the stronger pool too, both armies are destroyed.

**The final loss.** With `W` the winner's remaining fighting power and `L` the loser's (`L ≤ W`):

```
final loss = (L / W + 0.05) × L
```

It is taken from the winner's pool. Two equal armies give `1.05 × L`, more than the winner has, so both die. An army twice as strong loses `0.55 × L`, about 27% of what it had left; one five times as strong loses `0.25 × L`, about 5%. The fighting power compared here is the sum over a side's stacks of a strength number and a per-stack factor stored when the simulation was set up; those two fields were not traced further.

### Order within a round

`0x426bc0`, rounds 1 to 3. "Arrival round" is the round from the table above in which a walker or flyer can first strike; shooters have arrival round 0.

**1. Closing decision** (`0x4267c0`), made by each side every round. A side with no living walker or flyer that has arrived by this round cannot close. Otherwise it runs the rest of the battle on copies for every possible closing round from now to "never within three rounds" and keeps the one that leaves it best off (its own remaining pool, or minus the enemy's if it is wiped out). It closes now only if "now" is strictly the best; otherwise it keeps its distance for this round.

**2. Spells**, one per hero, as described [below](#spells-inside-the-simulator). The second caster chooses after the first spell has taken effect.

**3. Damage.** Both sides' damage is computed first and then applied, so within a round **neither side strikes first** and a stack that dies this round still deals its damage.

| Who closes | Attacker's damage | Defender's damage | Who takes the losses |
|---|---|---|---|
| Nobody | shooters only, at range | shooters only, at range | all stacks of each side |
| Attacker only | walkers and flyers that have arrived, plus shooters at range | every stack, at its melee rate | attacker: first the stacks that have arrived, the remainder over all stacks. Defender: all stacks |
| Defender only | every stack, at its melee rate | every stack, at its melee rate | all stacks of each side |
| Both | every stack, at its melee rate | every stack, at its melee rate | all stacks of each side |

"At its melee rate" means shooters fight hand to hand with their melee penalty. In the "attacker only" row the attacker's shooters are not hit until the stacks that charged are gone.

**4.** If a pool reaches zero the side is wiped out and the loop ends. After round 3 the [settlement](#the-arithmetic) is applied. **[code and assembly `0x426bc0`, `0x4267c0`, `0x426390`, `0x426170`; that the first record is the attacker follows from the return value of `0x4270c0`]**

### Spells inside the simulator

`0x425bd0`, called once for each side at the start of every round, so **each hero casts one spell per round**, the side that compares higher in `0x424960` first (not read; speed is the likely key). A side casts only if it has a hero with a spell book, mana left and an army left.

**When a side may cast** (`0x423ee0`). The side needs a hero with a Spell Book and mana. Casting is switched off for both sides when either hero wears the Orb of Inhibition (126), and for a battle on a Garrison object (33). On Cursed Ground only level 1 spells are allowed. The special terrain (Magic Plains, Magic Clouds, Fiery Fields, Rocklands, Lucid Pools) is passed to the school-level routine as on the battlefield.

**Mana is spent.** The simulator works on a copy of each hero's mana. When the battle is resolved for real, `0x426ee0` writes the remaining mana back into both hero records, so a computer hero comes out of a simulated battle with less mana. In the planning use of the simulator nothing is written back.

After a real resolution the winning hero, if it has Eagle Eye and a Spell Book, also learns one combat spell the loser knew, within its Eagle Eye and Wisdom limits (`0x426ee0`). **[code]**

Candidates are the hero's combat spells that it can pay for, with two filters: on [Cursed Ground](#candidate-spells) only level 1 spells, and if either hero wears Recanter's Cloak (83) only level 1 and 2. Each candidate gets a value in pool points, by the class bits of its spell flags:

| Class | Value |
|---|---|
| Single-target damage (`0x8000`) | Damage on the best enemy stack, capped at what that stack has left. Chain Lightning adds up to three more stacks at half damage each time; Frost Ring, Fireball, Inferno and Meteor Shower add neighbouring stacks (`0x424bf0`) |
| A second damage class (`0x10000`) | The same, but considered **in round 1 only** |
| Whole-field damage (`0x20000`) | `E − O`: damage to the enemy minus damage to its own stacks, and only if `O` is less than `E` and less than its own pool |
| Buffs, curses, Dispel (`0x40000`) | `0x425510`, `0x423c80`. For one stack: `pool points of the stack × the spell's AI value at the hero's school level × duration (at most 5 rounds) × the target's resistance factor / 500`. The AI value is the per-level column of the [spell table](../spells/). A beneficial spell is valued on the caster's own stacks, a harmful one on the enemy's; the best single stack, or the sum over all stacks when the spell is a mass spell at that school level. The protections, Anti-Magic, Dispel, Magic Mirror and Cure are considered only when the enemy has a hero with a spell book |
| Resurrection, Animate Dead (`0x80000`, spells 38 and 39) | On the best stack: creatures raised, capped by that stack's losses, times its points per creature |

The spell with the highest value is cast and its cost is taken from the hero's mana. If the enemy army contains Familiars, the enemy hero gains a fifth of that cost. Damage is then removed from the pools exactly like combat damage; a whole-field spell is applied to the caster's own stacks as well.

No mana factor and no random factor are applied here; the spell with the largest value is taken each round. Summoning spells and Teleport are in none of the classes and are never cast in a simulated battle. **[code; which spells carry `0x10000` was not listed]**


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
