---
title: Factions and towns
parent: English
nav_order: 2
lang: en
---

# Factions and towns
{: .no_toc }

Building costs and prerequisites for the nine town types. Creatures of each town are in the [creature table](../creatures/); hero classes in [Heroes](../heroes/).

1. TOC
{:toc}

> **HotA 1.8.1:** adds three towns (Cove, Factory, Bulwark) whose building lists are not read; only their [creatures](../hota/#new-creatures) are. Phoenix and Firebird growth and several prices differ, see [HotA differences](../hota/#creatures).

Related: [what the computer builds and in what order](../ai-towns/), [Arrow Towers by fortification level](../combat/#arrow-towers-and-war-machines), [moat damage by town](../combat/#siege-partial).

## Where the data comes from

- **Costs** are from `BUILDING.TXT` **[data]**.
- **Prerequisites** are not in any text file. They are static lists inside `Heroes3.exe`, one per town type, starting at `0x63ec80` and running to `0x63fbc4`. At start-up `0x4eb730` expands them into bit masks, adding each prerequisite's own prerequisites, which is the table the town screen and the [town AI](../ai-towns/#score-and-choice) use. **[data, executable]**

The tables below show the direct prerequisites as stored. A building is available when everything it requires, directly and indirectly, is built, the town's map settings allow it, and nothing else was built in the town that day.

Building numbers are the engine's: 0–4 Mage Guild, 5 Tavern, 6 Shipyard, 7–9 Fort line, 10–13 Town Hall line, 14 Marketplace, 15 Resource Silo, 16 Blacksmith, 17 and 21–23 town specials, 18–19 and 24–25 horde buildings, 26 Grail, 30–36 dwellings, 37–43 upgraded dwellings. Dwellings are labelled as the game's table labels them.

## Rules that are the same in every town

Read off the lists:

- Town Hall needs the Tavern.
- City Hall needs Town Hall, Marketplace, Blacksmith and Mage Guild level 1.
- Capitol needs City Hall and the Castle.
- Citadel needs the Fort, Castle needs the Citadel.
- Resource Silo needs the Marketplace.
- The first dwelling needs the Fort.
- Each Mage Guild level needs the one below it.

## Buildings by town

{% include town_buildings.html lang="en" %}
