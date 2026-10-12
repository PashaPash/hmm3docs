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

### Battle behaviour

Difficulty switches parts of the battle logic on and off for every non-human side, including neutral monsters. See [AI: battle](../ai-battle/#what-difficulty-changes).

## Coverage of AI decisions

What the computer player decides, and where it is described. "Partly" means the structure is described but some values or branches were not read.

| Decision | Status | Where |
|---|---|---|
| Battle: action of each stack, melee and ranged | covered | [AI: battle](../ai-battle/) |
| Battle: hero spell | covered for candidates, scoring and timing; about half of the per-spell evaluators only listed | [AI: battle](../ai-battle/#hero-spells) |
| Battle: creature spells, retreat, surrender | covered | [AI: battle](../ai-battle/) |
| Battle: tactics-phase placement | partly (shooters only) | [AI: battle](../ai-battle/#shooters) |
| Battle: resolution without a battlefield (no human side) | structure covered; per-round arithmetic **not read** | [AI: battle](../ai-battle/#battles-without-a-battlefield) |
| Neutral stacks: join, flee, fight, split, growth | covered | [AI: neutral monsters](../ai-neutral/) |
| Hero: where to go | covered for the choice rule; object values partly | [AI: adventure map](../ai-adventure/) |
| Hero: whether a fight is worth it | covered for multipliers and outcome use; simulator structure covered, its arithmetic **not read** | [AI: adventure map](../ai-adventure/#valuing-a-fight) |
| Hero: returning to defend a town, emergency garrison purchase | covered | [AI: adventure map](../ai-adventure/#its-own-towns) |
| Hero: merging armies with another hero | partly | [AI: adventure map](../ai-adventure/#enemy-heroes) |
| Hero: Town Portal, Castle Gate, Water Walk in path planning | covered | [AI: adventure map](../ai-adventure/#adventure-spells-in-path-planning) |
| Hero: casting Fly and Dimension Door | no code found that does it; unverified | [AI: adventure map](../ai-adventure/#fly-and-water-walk) |
| Hero: obelisks and digging for the Grail | covered; how the dig position is determined **not read** | [AI: adventure map](../ai-adventure/#obelisks-and-the-grail) |
| Hero: boarding boats | covered; building ships and Summon Boat not found | [AI: adventure map](../ai-adventure/#boats) |
| Hero: level-up skill choice | covered for most skills; the new-versus-upgrade test **not read** | [AI: adventure map](../ai-adventure/#level-up-choices) |
| Hero: artifact exchange between two heroes in a town | covered; equipping from the backpack on pickup **not read** | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |
| Player: hiring heroes | covered: limits, which tavern hero, which town | [AI: adventure map](../ai-adventure/#hiring-heroes) |
| Town: what to build | covered; upgraded dwelling and horde values only listed | [AI: towns](../ai-towns/) |
| Town: recruiting | purchase order, army gain and displaced stack covered; the garrison versus hero split only for the victory-town case | [AI: towns](../ai-towns/#which-creatures-are-bought-first) |
| Economy: resource valuation | covered | [AI: adventure map](../ai-adventure/#what-resources-are-worth) |
| Economy: Marketplace trades | covered except the selling order | [AI: towns](../ai-towns/#trading-at-the-marketplace) |
| Economy: gifts to allies | covered | [AI: towns](../ai-towns/#gifts-to-allies) |
| Economy: war machines | covered | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |
| Economy: Mage Guild levels | covered | [AI: towns](../ai-towns/#when-a-hero-visits-its-own-town) |
| Economy: Black Market, Magic University | covered | [AI: adventure map](../ai-adventure/#object-values-that-are-readable) |
| Economy: Artifact Merchants in towns | **not read** | |

## Two value columns

`CRTRAITS.TXT` gives each creature two numbers ([table](../creatures/)):

- **Fight Value** is used inside battles to weigh damage dealt and taken.
- **AI Value** is used on the adventure map: army strength for the join/flee decision of wandering monsters is `Σ AI Value × count`, scaled by the hero's Attack and Defence. See [neutral monsters](../ai-neutral/).

Per-class `Aggression` from `HCTRAITS.TXT` and the per-spell AI values from `SPTRAITS.TXT` are read by adventure-map and spell-selection code that is not decoded yet.
