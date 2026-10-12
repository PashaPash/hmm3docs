---
title: "AI: towns"
parent: English
nav_order: 10
lang: en
---

# AI: town building and recruitment
{: .no_toc }

1. TOC
{:toc}

## Summary

- Each building gets a **direct value**. Only income, dwellings, fortifications, hordes and a few town specials have one.
- A building is scored by `value × 1000 / cost`, where the cost includes **every prerequisite still missing** and is measured with the [resource weights](../ai-adventure/#what-resources-are-worth).
- The score of a goal is credited to every building on its prerequisite chain, and the best building that can be built today wins.
- Mage Guilds, Marketplace, Tavern and Blacksmith have no direct value; in this routine they are built only as prerequisites. Mage Guilds and the Blacksmith are also built [when a hero visits](#when-a-hero-visits-its-own-town).
- On Easy and Normal a computer player's town builds at most **every other day**.

## The economy phase of a turn

Building numbers, costs and prerequisites are in [Factions and towns](../towns/). HotA's three new towns are not covered ([what is known](../hota/)).

`0x428dd0`, once per computer player per turn:

1. Repeat `0x42ae00` until it finds nothing to buy. Each call builds one building.
2. Decide whether to hire a hero (`0x431360`, see [hiring heroes](../ai-adventure/#hiring-heroes)).
3. Recompute the resource weights (`0x428740`).
4. If the player has a town with a Marketplace, send surplus resources to allies (`0x429110`, see [gifts](#gifts-to-allies)).

## One build per town per day, or per two days

`0x5bede0` marks a town when something is built in it; `0x4c7fe0` clears the mark at the start of each day.

| Difficulty | Mark set by a build | Effect |
|---|---|---|
| Hard, Expert, Impossible | cleared every day | one building per town per day |
| Easy, Normal | set to 2 and reduced by 1 each day for a computer player's town | **one building per town every two days** |

**[code; the test that separates computer-owned towns from human-allied ones is a helper that was not read]**

## Direct value of a building

`0x42ae00`. Building numbers are the engine's (0–43).

| Building | Direct value | Routine |
|---|---|---|
| Town Hall line (10–13) | Extra weekly gold × gold weight: Village Hall 3500, Town Hall 3500, City Hall 7000, Capitol 14000 | `0x42b8b0` |
| Dwellings (30–36) | Only when the town is not marked as threatened. `AI Value × weekly growth` of the creature. From day 5 of the week the growth is doubled and what is already waiting is added. The cost of then buying those creatures is added to the cost side | `0x42b520` |
| Upgraded dwellings (37–43) | `(AI Value upgraded − AI Value base) × number of base creatures on hand` (from day 5, with the coming growth). The price difference for upgrading that many is added to the cost side | `0x42b5b0` |
| Citadel, Castle (8, 9) | From day 5: sum of the AI Values of the town's creatures that will grow, with their purchase cost on the cost side | `0x42b670` |
| Horde buildings (18, 19, 24, 25) | `AI Value × the extra weekly growth` the building gives, with the price of those extra creatures on the cost side. The upgraded-creature horde is skipped when its building is already in place | `0x42b790`, `0x42b800` |
| Resource Silo (15) | Seven days of its output at the resource weights; not when the town is marked as threatened | |
| Rampart Treasury (22) | Only on day 7; proportional to the gold the player holds | |
| Tower: special 21 | 100 | |
| Necropolis: special 17 | 10 | |
| Necropolis: special 21 | Grows with the number of the player's heroes of one particular class | |
| Stronghold: special 17 | 5000, only when the town is marked as threatened and has a visiting hero | |
| Fortress: specials 21, 22 | Garrison's `AI Value` total / 20, only when the town is marked as threatened | |
| Grail (26) | Never chosen here; built when a hero carrying the Grail visits (see below) | |
| Everything else | 0 | |

If the scenario's victory condition is to build a given Town Hall or Fort level in this town, the matching buildings get +5,000,000.

## Score and choice

For every building with a positive direct value:

1. Collect its missing prerequisites from the per-town dependency table (`0x697798`).
2. Add up the costs of the whole chain.
3. `score = value × 1000 / Σ (cost[r] × weight[r])` (`0x42a150`). If a needed resource cannot be paid and the player has no income of it, the routine checks whether it can be obtained by trading; if not, the goal is dropped.
4. Add the score to **every building in the chain**.

Then, over all the player's towns that may still build today, the buildable building with the highest accumulated score is built, provided the player keeps a reserve the routine holds back for planned purchases. The reserve check is skipped for the Town Hall line, Marketplace and Resource Silo. **[code]**

A cheap building that unlocks several valuable ones collects all their scores, which is how Mage Guild level 1, Blacksmith or Marketplace get built despite having no value of their own.

## Which creatures are bought first

`0x42d690` and `0x42d420`, used whenever the AI recruits: for a visiting hero, for the garrison, and for the emergency purchase when a town is in danger.

1. Stacks of the same creature in the receiving army are merged first, to free slots.
2. For every creature on offer, work out how many can be afforded: the smaller of the number available and what each resource allows.
3. Compute the **gain** of adding that many to this army (`0x42c830`, which takes free slots and the stacks it would have to displace into account).
4. When the purchase is charged against the player's plans, subtract the cost at the [resource weights](../ai-adventure/#what-resources-are-worth), but never more than three quarters of the gain.
5. Buy the option with the largest result, then start again from step 2 until nothing has a positive result.

So the order is not "highest level first": it is whichever purchase adds the most army value for its weighted cost at that moment, bought to the limit of the purse, then re-evaluated. A resource the player is short of makes creatures that need it less attractive, but can never cancel more than 75% of their value. **[code]**

### The gain of adding a stack

`0x42c830`, the value used in step 3.

```
gain = AI Value × number bought
```

adjusted as follows:

- **Map speed.** If the creature is slower than the slowest stack already in the army, a term taken from the [land movement table](../adventure/#on-land) and scaled by `army AI Value + 500` is applied, so a slow recruit that would cut the hero's daily movement is worth less. **[the term is read; that it lowers the gain is inferred]**
- **Already in the army.** If the army has a stack of that creature, the new units join it and the gain stands.
- **Free slot.** Otherwise a free slot is used, provided the army has fewer than six stacks in use (or the caller allows a seventh).
- **Mixing rule.** A creature of a different alignment that would cost the army morale is refused a free slot when it is small: when ten times its value is no more than the value of the army it would join.
- **No free slot.** The routine picks a stack to push out (`0x42c690`) and the gain is reduced by that stack's `AI Value × count`. If no stack can be pushed out, the gain is 0.

### Which stack is pushed out

`0x42c690`. Among the stacks already in the army, the one with the **lowest total `AI Value × count`** is replaced, with two protections for shooters:

- if the army has exactly one stack of shooters, that stack is never the one pushed out;
- when the caller asks to keep ranged strength and the army has four or more shooter stacks, only a shooter stack may be pushed out.

When the purchase would break the mixing rule above, only stacks of the odd alignment are candidates.

## Trading at the Marketplace

The computer player does not trade to make a profit or to balance its stock. It trades only **to complete a specific purchase**, from inside the scoring routine `0x42a150`.

1. **Trigger.** While pricing a building chain, a resource counts as blocking when the stock is below the cost and the player has **no income** of that resource. With income, the AI simply waits.
2. **What can be sold** (`0x42a2b0`). For every other resource: `spare = stock − cost of the planned purchase − cushion`, where the cushion is the amount already reserved for other planned purchases, at least 20. The spare is further limited to the surplus from the [resource weights](../ai-adventure/#what-resources-are-worth) (`have − need`). A resource with no positive spare is not sold.
3. **Where** (`0x42a580`). The player needs at least one Marketplace. The number of Marketplaces, up to 10, sets the exchange rate as it does for a human. A Marketplace the player could build today also counts if it has gold income.
4. If there is something short and something spare, the routine sells spare resources to cover the shortage. If the shortage cannot be covered, the purchase goal is dropped for this turn.

The order in which spare resources are sold was not read. **[code]**

## Gifts to allies

`0x429110`, called at the end of the economy phase for every player on the same team, computer allies first and human allies after. It runs only if the giver has a town with a **Marketplace**.

For each resource:

```
surplus = have − need                      the same figures as in the resource weights
gift    = min(surplus, (my stock − ally's stock) / 2)
keep at least 10000 gold, or 20 of any other resource
subtract what is reserved for my own planned purchases
drop the gift if it is under 1000 gold, or under 5 of another resource
drop the gift if it is less than 5 × what the ally already has
```

- The last line means gifts go only to an ally who is nearly out of that resource: the amount must be at least five times the ally's current stock.
- To an allied **computer** player the gift is also capped at what that ally is short of (`need − have`, recomputed for the ally first).
- To an allied **human** player the amount is sent as computed and a message is shown.

**[code; the `min` in the second line is read from a garbled decompilation and is inferred]**

## When a hero visits its own town

`0x5253d0` runs when an AI hero enters a town of its own player:

- If the hero carries the Grail and the town has none, the Grail building is built.
- Creatures are recruited into the hero's army (`0x525200`, `0x42ba60`). On Hard and above, and if the town has not built today, the routine may also build the one dwelling (buildings 30–43) that adds the most to this hero's army right now.
- A **Mage Guild level** is built for the visiting hero (`0x42beb0`). The next level is built when all of these hold:
  - the guild is below level 5 and below `the hero's Wisdom level + 2`, so a hero without Wisdom gets a guild up to level 2, Basic up to 3, Advanced up to 4, Expert up to 5;
  - the hero has more than 2 Spell Power and more than 2 Knowledge; this is waived for the first level if the hero lacks two particular basic spells;
  - no other town of the player already has a higher guild that this hero could still use and that could be built up instead;
  - the player can pay and the town has not built today.

  This is how Mage Guilds get built beyond their role as prerequisites: they follow heroes who can use them.
- If the scenario is won by holding a particular town, and this hero is not the player's strongest, it stops there and **leaves its army in that town's garrison** (`0x525200`). Above Easy, with at least two heroes, and only when the town is not marked as threatened.
- In a Conflux with the **Magic University**, the hero learns the skills on offer that are worth it (`0x524ed0`): it needs fewer than eight skills and the player at least 2000 gold, and each skill is judged by the same value as in [level-up choices](../ai-adventure/#level-up-choices).
- A Spell Book is bought for 500 gold if the town has a Mage Guild and the hero has none.
- Creatures in the hero's army are upgraded where the upgraded dwelling exists and the player can pay.
- A stat building is built on the spot when it is worth more to this hero than it costs at the resource weights:

  | Town | Building | Compared with |
  |---|---|---|
  | Tower | special 23 (+1 Knowledge) | the hero's value of a Knowledge point |
  | Inferno | special 23 (+1 Spell Power) | the hero's value of a Spell Power point |
  | Dungeon | special 23 (+1000 experience) | `1000 ×` the hero's value of one experience point |
  | Stronghold | special 23 (+1 Attack) | experience for the hero's next level × value of one experience point |
  | Fortress | special 17 (+1 Defence) | the same |
  | Conflux | special 21 (Magic University) | a skill-value routine |

- Above Easy, the hero buys the town's **war machine** if it does not have one (`0x525ca0`): the machine sold by that town's Blacksmith, and in a Stronghold also the Ballista from the Ballista Yard. The machine must be usable by the hero and affordable in full. If the Blacksmith itself is missing and can be built today, the routine builds it first and then buys.
- Above Easy, the garrison hero and the visiting hero **exchange artifacts** (`0x433fe0`, run once in each direction). For each equipped artifact the routine takes it off, checks whether the other hero's total artifact value would rise by more than this hero's falls (`0x433e20`, `0x433bb0`), and either hands it over or puts it back. Backpack artifacts are passed on when the other hero can make use of them.

## Not decoded yet

- The general split of armies between a town garrison and heroes; only the victory-town case above was read.
- Artifact Merchants in towns (the Black Market object is covered under [object values](../ai-adventure/#object-values-that-are-readable)), and the order in which spare resources are sold at the Marketplace.
- The threat mark is described under [how a town gets its threat mark](../ai-adventure/#how-a-town-gets-its-threat-mark); the same pass buys emergency garrison troops before any building is chosen.
