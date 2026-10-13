---
title: Adventure map
parent: English
nav_order: 7
lang: en
---

# Adventure map
{: .no_toc }

Hero movement so far. Map objects, economy and week events are not written here yet; weekly monster growth and the new-month roll are in [neutral monsters](../ai-neutral/#growth-and-new-stacks).

1. TOC
{:toc}

## Movement points per day

The computer's use of these numbers: a target counts as "near" within 21% of the daily total ([AI: adventure map](../ai-adventure/#step-4-choose)), and an enemy hero threatens a town within its daily movement plus 800 ([threat mark](../ai-adventure/#how-a-town-gets-its-threat-mark)).

`0x4e4990`.

### On land

```
points = table[speed of the slowest creature] × (1 + Logistics) + flat bonuses
```

{% include movement.html lang="en" %}

From `MOVEMENT.TXT` **[data]**. Speeds below 3 continue the same table downwards (1300, 1360, 1430).

- The speed used is the creature's **base** speed from the creature table. If the hero is a specialist in that creature, or in the creature it upgrades to, that stack counts as 1 faster.
- Logistics: 10% / 20% / 30% (table `0x63ea68`). A Logistics specialist multiplies the percentage by `1 + 0.05 × hero level`.
- Flat bonuses, added after the multiplication, so Logistics does not scale them: artifact 98 (Boots of Speed) +600, artifact 70 (Equestrian's Gloves) +300, a visit to Stables +400. The amounts are the bonus column of `MOVEMENT.TXT`.
- An empty army uses the top of the table.

### At sea

Creature speed is ignored on a boat.

```
points = Navigation base + specialist bonus + flat bonuses
```

| Navigation | none | Basic | Advanced | Expert |
|---|---|---|---|---|
| Base | 1500 | 2250 | 3000 | 3750 |

- A Navigation specialist adds `hero level × 1500 / 20`, that is 75 points per level.
- Flat bonuses: +500 for each Lighthouse object the player has flagged **[inferred: the counting helper was not read]**, +500 for each Castle town of the player with the Lighthouse building, +500 for artifact 123 (Sea Captain's Hat), +1000 for artifact 71 (Necklace of Ocean Guidance).

**[code]**

## Cost of a step

`0x4b1740`. Costs are in the same movement points.

| Terrain | No Pathfinding | Basic | Advanced | Expert |
|---|---|---|---|---|
| Dirt, grass, subterranean, lava, water | 100 | 100 | 100 | 100 |
| Rough | 125 | 100 | 100 | 100 |
| Sand, snow | 150 | 125 | 100 | 100 |
| Swamp | 175 | 150 | 125 | 100 |
| Dirt road | 75 | 75 | 75 | 75 |
| Gravel road | 65 | 65 | 65 | 65 |
| Cobblestone road | 50 | 50 | 50 | 50 |

Table `0x63e510`.

- A **road** replaces the terrain cost entirely; Pathfinding does not make roads cheaper.
- **Native terrain**: if the tile's terrain is native to every creature in the army, the step costs 100 whatever the terrain, except on one special ground type.
- **Nomads** in the army make sand cost the same as dirt.
- **Diagonal** steps cost ×1.414.
- **Last-step rule**: if the hero has enough points left for the straight cost of the tile but not for the diagonal cost, the diagonal step is charged only the straight cost.
- **Fly** and **Water Walk** charge a fixed cost per step by spell level, 140 / 140 / 120 / 100 for none / Basic / Advanced / Expert (table `0x6778ac`). Artifact 72 (Angel Wings) and artifact 90 (Boots of Levitation) act as the Expert spell. Flying over ordinary passable land charges the smaller of the terrain cost and the flying cost.
- On water, one special ground type cuts the cost to two thirds.

**[code]**
