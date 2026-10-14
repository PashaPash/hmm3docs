---
title: "AI: overview"
parent: English
nav_order: 8
lang: en
---

# AI: overview

## Difficulty

The game stores one difficulty value, 0 (Easy) to 4 (Impossible), at offset `0x1f6d8` of the main game object. It is read in 48 functions. **[code]**

### Starting resources

Two tables in the executable are indexed by difficulty, seven resources each. **[data, `Heroes3.exe` `0x678170` and `0x6781fc`]** Which table belongs to whom is **[inferred]** from the human values every player knows.

| Difficulty | Human: wood, ore | Human: mercury, sulfur, crystal, gems | Human: gold | AI: wood, ore | AI: other four | AI: gold |
|---|---|---|---|---|---|---|
| Easy | 30 | 15 | 30000 | 5 | 2 | 5000 |
| Normal | 20 | 10 | 20000 | 10 | 4 | 7500 |
| Hard | 15 | 7 | 15000 | 15 | 7 | 10000 |
| Expert | 10 | 4 | 10000 | 15 | 7 | 10000 |
| Impossible | 0 | 0 | 0 | 15 | 7 | 10000 |

### Adventure map

Difficulty sets how many heroes a computer player hires (2 / 3 / 4 / 5 / 6 per player) and how strong it assumes a human army to be (×0.5 on Easy and Normal, ×1.0 on Hard, ×1.25 above). It also sets an owner factor: on Easy the AI prefers other computer players' property to a human's, on Expert and Impossible the reverse. See [AI: adventure map](../ai-adventure/#who-the-ai-goes-after).

### Towns

On Easy and Normal a computer player's town builds at most once every two days; from Hard up, once a day. See [AI: towns](../ai-towns/).

### The Grail

The share of the puzzle a computer player needs before it goes digging depends on difficulty: never on Easy, half on Normal, a quarter on Hard, none on Expert and Impossible. See [where the computer decides to dig](../ai-adventure/#where-the-computer-decides-to-dig).

### Battle behaviour

Difficulty switches parts of the battle logic on and off for every non-human side, including neutral monsters. See [AI: battle](../ai-battle/#what-difficulty-changes).

## Player personality: Warrior, Builder, Explorer

The map editor lets the author set an "AI tactic" for each player: Random, Warrior, Builder or Explorer.

**Where the value goes.** The map header parser (`0x4c5630`) reads it and stores it in the player's map attributes (offset +4 of a 0x44-byte record, game object `+0x1f90c + player × 0x44`). In `Heroes3.exe` no code reads that field afterwards: its address does not occur anywhere in the executable, and none of the 27 routines that touch the attribute records reads offset +4. All of those are setup and scenario-screen routines.

**What the game uses instead.** At the start of a game (`0x4bfe70`) every player gets a personality number in its own record (player `+0x34`):

| Player | Personality |
|---|---|
| Human | 3 |
| Computer | `rand(0,2)`: 0 Warrior, 1 Builder, 2 Explorer |

So in the unmodified game a computer player's personality is random and the map's setting has no effect.

**What the personality changes.** Two readers of the number were found:

- **Hero movement** (`0x4e4990`). A hero of a computer player gets extra movement points each day on Expert and Impossible difficulty: **+75**, and **+125 if the player is an Explorer**. This applies to the first six player colours only (Red to Purple); Teal and Pink do not get it. See [hero movement](../adventure/#on-land).
- **Thieves' Guild** (`0x5dda10`): the personality name shown for each player.

No routine in the adventure-map, town or battle AI was found to read it. This was checked three ways: by the field's address in the raw bytes of the executable (three sites: the roll, hero movement, Thieves' Guild); by listing every read of that offset in the decompile of all routines that handle player records; and by scanning the machine code of all 318 functions that touch player data for any access at offset 0x34, which found none in the AI code. The hero-hiring limits, which community descriptions tie to the Explorer, are indexed by difficulty (`0x431360`). Warrior and Builder therefore differ only by the name shown in the Thieves' Guild. **[code and assembly; the names for 0, 1 and 2 are taken from the HotA mapping below and the Thieves' Guild order]**

**Experiment.** Run on 2026-10-13 in a recompiled build of the same `Heroes3.exe` (the Mac port; floating point in doubles, so not the original binary under Windows). One map, random seed held fixed, Expert difficulty, 28 days, one computer player with its personality forced to 0, 1 and 2 in three runs, the other computer players at 0. Sampled after every turn for every player: hero count, hero levels, maximum movement, army strength, gold, town count, buildings built, and a fingerprint of hero positions, experience, armies, town building masks and resources.

| Compared runs | Result |
|---|---|
| Warrior, repeated | identical in every sample for 28 days |
| Warrior and Builder | identical in every sample for 28 days, all players |
| Warrior and Explorer | first difference after the first turn: the hero's maximum movement is 1625 instead of 1575, nothing else that day; the runs then diverge |

On day 29 the tested player had 3 heroes, 2 towns and 35 buildings as Warrior or Builder, and 4 heroes, 3 towns and 45 buildings as Explorer. This is one trajectory on one map; whether all the later Explorer differences follow from the extra movement was not tested. **[experiment on a recompiled build; one map, one seed]**

> **HotA 1.8.1:** `HotA.dll` hooks the roll in the new-game routine. If the map's value is Warrior, Builder or Explorer, the personality is set to it; only "Random" keeps the roll. See [HotA differences](../hota/#player-personality).

## Coverage of AI decisions

What the computer player decides, and where it is described. "Partly" means the structure is described but some values or branches were not read.

| Decision | Status | Where |
|---|---|---|
| Battle: action of each stack, melee and ranged | covered | [AI: battle](../ai-battle/) |
| Battle: hero spell | covered: candidates, scoring, timing and the per-spell evaluators | [AI: battle](../ai-battle/#hero-spells) |
| Battle: creature spells, retreat, surrender | covered | [AI: battle](../ai-battle/) |
| Battle: tactics-phase placement | covered | [AI: battle](../ai-battle/#tactics-phase) |
| Battle: resolution without a battlefield (no human side) | covered, including the final loss and the one spell per hero per round | [AI: battle](../ai-battle/#battles-without-a-battlefield) |
| Neutral stacks: join, flee, fight, split, growth | covered | [AI: neutral monsters](../ai-neutral/) |
| Hero: where to go | covered for the choice rule; object values partly | [AI: adventure map](../ai-adventure/) |
| Hero: whether a fight is worth it | covered for multipliers and outcome use; simulator covered | [AI: adventure map](../ai-adventure/#valuing-a-fight) |
| Hero: returning to defend a town, emergency garrison purchase | covered | [AI: adventure map](../ai-adventure/#its-own-towns) |
| Hero: merging armies with another hero | partly | [AI: adventure map](../ai-adventure/#enemy-heroes) |
| Hero: Town Portal, Castle Gate, monoliths, gates, whirlpools, Water Walk in path planning | covered | [AI: adventure map](../ai-adventure/#adventure-spells-in-path-planning) |
| Hero: casting Fly, Water Walk and Dimension Door | covered | [AI: adventure map](../ai-adventure/#fly-water-walk-and-dimension-door) |
| Hero: obelisks and digging for the Grail | covered, including the difficulty threshold; the choice among uncovered tiles **not read** | [AI: adventure map](../ai-adventure/#obelisks-and-the-grail) |
| Hero: order of moves within a turn, patrolling heroes | covered | [AI: adventure map](../ai-adventure/#a-computer-players-turn) |
| Hero: danger map from enemy heroes | covered | [AI: adventure map](../ai-adventure/#danger-from-enemy-heroes) |
| Hero: boarding boats, buying boats, Summon Boat | covered | [AI: adventure map](../ai-adventure/#boats) |
| Hero: level-up skill choice | covered | [AI: adventure map](../ai-adventure/#level-up-choices) |
| Hero: artifact exchange between two heroes in a town | covered, with the [gain rule](../ai-adventure/#wearing-and-replacing) for worn artifacts | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |
| Player: hiring heroes | covered: limits, which tavern hero, which town | [AI: adventure map](../ai-adventure/#hiring-heroes) |
| Town: what to build | covered | [AI: towns](../ai-towns/) |
| Town: recruiting | purchase order, army gain, displaced stack and the [exchange with the garrison](../ai-towns/#army-exchange-with-the-garrison) covered | [AI: towns](../ai-towns/#which-creatures-are-bought-first) |
| Economy: resource valuation | covered | [AI: adventure map](../ai-adventure/#what-resources-are-worth) |
| Economy: Marketplace trades | covered | [AI: towns](../ai-towns/#trading-at-the-marketplace) |
| Economy: gifts to allies | covered | [AI: towns](../ai-towns/#gifts-to-allies) |
| Economy: war machines | covered | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |
| Economy: Mage Guild levels | covered | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |
| Economy: Black Market, Magic University | covered | [AI: adventure map](../ai-adventure/#object-values-that-are-readable) |
| Economy: Artifact Merchants in towns | covered | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |

## Two value columns

`CRTRAITS.TXT` gives each creature two numbers ([table](../creatures/)):

- **Fight Value** is used inside battles to weigh damage dealt and taken.
- **AI Value** is used on the adventure map: army strength for the join/flee decision of wandering monsters is `Σ AI Value × count`, scaled by the hero's Attack and Defence. See [neutral monsters](../ai-neutral/).

The per-spell AI values from `SPTRAITS.TXT` are used by the [battle simulator](../ai-battle/#spells-inside-the-simulator) for buffs and curses. The per-class `Aggression` from `HCTRAITS.TXT` sets each [hero's own factor](../ai-adventure/#the-heros-own-factor) in the fight estimate.
