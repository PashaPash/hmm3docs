---
title: HotA 1.8.1 differences
parent: English
nav_order: 14
lang: en
---

# Horn of the Abyss 1.8.1 differences
{: .no_toc }

Only differences that could be confirmed from files. Everything else on this site describes the unmodified Shadow of Death executable.

1. TOC
{:toc}

## What was compared, and what was not

- **Compared:** the text tables in `HotA_lng.lod` against the same tables in `H3ab_bmp.lod`. That archive is a normal LOD and reads with `tools/lod.py`; the numbers below are a mechanical diff of the two sets. **[data]**
- **Not compared:** code. HotA runs its own executable (`h3hota.exe`, a different build from the GOG `Heroes3.exe` analysed here, so addresses on this site do not carry over) and patches it in memory from `HotA.dll`. None of the AI, combat or map rules on the other pages has been checked against HotA.
- **Not read:** `HotA.lod` (its directory is obfuscated) and `HotA.dat`, which hold the new towns' creatures and objects. So nothing here covers Cove, Factory or Bulwark units.
- Whether `HotA.dll` overrides any of these table values at run time is **[unverified]**. The values match changes HotA is known for, which suggests the tables are the ones in use.

## Creatures

Only values that differ. SoD → HotA.

| Creature | Change |
|---|---|
| Angel | cost 3000 gold → 3000 gold + 1 gems |
| Archangel | cost 5000 gold → 5000 gold + 3 gems |
| Cerberus | maximum damage 5 → 7 |
| Lizardman | hit points 12 → 14, minimum damage 1 → 2, growth 8 → 9, Fight Value 115 → 137, AI Value 126 → 151 |
| Lizard Warrior | hit points 12 → 15, attack 5 → 6, defence 7 → 8, maximum damage 3 → 5, growth 8 → 9, cost 130 → 140, Fight Value 130 → 174, AI Value 156 → 209 |
| Serpent Fly | attack 6 → 7, defence 8 → 9, Fight Value 205 → 215, AI Value 256 → 268 |
| Dragon Fly | attack 6 → 8, defence 8 → 10, Fight Value 205 → 250, AI Value 256 → 312 |
| Psychic Elemental | cost 750 → 950 |
| Magic Elemental | cost 800 → 1200 |
| Firebird | growth 2 → 1, cost 1500 → 2000, Fight Value 3248 → 3097, AI Value 4547 → 4336 |
| Phoenix | growth 2 → 1, cost 2000 → 3000 gold (plus 1 mercury as before) |
| Ballista | cost 2500 → 1500 |

AI Value only (changes how the computer weighs these units, not how they fight): Monk 485 → 582, Naga 2016 → 1814, Efreet Sultan 1848 → 2343 (and Fight Value 1584 → 1802), Ghost Dragon 4696 → 4919 (Fight Value 3228 → 3346), Scorpicore 1589 → 1685, Red Dragon 4702 → 5003, Cyclops King 1443 → 1544, Faerie Dragon 19580 → 30501.

Size of random wandering stacks changed for: Gorgon and Mighty Gorgon (smaller), Serpent Fly and Dragon Fly (larger), Basilisk and Greater Basilisk (larger), Fire, Energy, Psychic and Magic Elementals (smaller), Phoenix (smaller), Sharpshooter (larger).

## Spells

| Spell | Change |
|---|---|
| Fire Wall | damage per Spell Power 10 → 15 |
| Armageddon | damage per Spell Power 50 → 40 |
| Protection from Air, Fire, Water, Earth | damage let through: 70% / 70% / 50% / 50% → 50% / 50% / 25% / 25% (none / Basic / Advanced / Expert) |
| Summon Fire Elemental, Summon Earth Elemental | summoned per Spell Power 2 / 2 / 3 / 4 → 2 / 2 / 2 / 3 |

No change in mana costs, spell levels or per-spell AI values for the 70 hero spells.

## Hero classes

The 18 original classes are unchanged: starting skills, primary skill chances, secondary skill weights and `Aggression` are identical. The table has six more rows: Captain, Navigator, Mercenary, Artificer, Chieftain, Elder.

## Creature banks

| Bank | Change |
|---|---|
| Naga Bank, all levels | the resource part of the reward is gems instead of sulfur, same amounts |
| Dragon Fly Hive, all levels | upgrade chance for a guard stack 50% → 0% |

Guards, level chances and the other rewards of the 11 original banks are the same. New HotA banks are not in this table.

## How this interacts with the rest of the site

Under the SoD rules described here, some of these numbers feed directly into decisions:

- Fight Value drives [battle AI](../ai-battle/#what-a-unit-is-worth) scoring; AI Value drives [join or flee](../ai-neutral/#before-the-fight-join-flee-or-fight) and [stack splitting](../ai-neutral/#how-the-stack-is-split-for-battle).
- A Dragon Fly Hive with a 0% upgrade chance never has an upgraded guard stack under the [bank generation](../ai-neutral/#creature-banks) rule.

Whether HotA keeps those rules is exactly the part that has not been checked.
