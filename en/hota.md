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
- **Not compared:** code. HotA runs its own executable (`h3hota.exe`, a different build from the GOG `Heroes3.exe` analysed here, so addresses on this site do not carry over) and patches it in memory from `HotA.dll`. Apart from the [battle AI check below](#battle-ai-code), the AI, combat and map rules on the other pages have not been checked against HotA.
- **Read in part:** `HotA.dat`. Its creature records give the stats of the 50 new creatures, see [New creatures](#new-creatures). Its bank records give the twelve new creature banks, see [New creature banks](#new-creature-banks). Its other record types (heroes, objects, classes) are not decoded.
- **Not read:** `HotA.lod`, whose directory is obfuscated.
- Whether `HotA.dll` overrides any of these table values at run time is **[unverified]**. The values match changes HotA is known for, which suggests the tables are the ones in use.

## Creatures

The SoD values are in the [creature table](../creatures/).

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

## New creatures

Read from `HotA.dat` with `tools/hota_dat.py` **[data]**. The file is a list of named records; the 50 records named `monst150` to `monst199` each carry a 116-byte image of the engine's own creature structure, so the fields are the same ones as in the [SoD creature table](../creatures/). Town numbers 9, 10 and 11 are Cove, Factory and Bulwark.

- These are the values stored in the file. Special abilities are code in `HotA.dll` and are not described here.
- Factory has two level 7 lines (Couatl and Dreadnought), so it has 16 creatures where other towns have 14.
- Ids 150 and 152 are the Cannon and an "Electric Tower", the war machine and tower used by the new towns.

{% include hota_creatures.html lang="en" %}

## Spells

The SoD values are in the [spell table](../spells/).

| Spell | Change |
|---|---|
| Fire Wall | damage per Spell Power 10 → 15 |
| Armageddon | damage per Spell Power 50 → 40 |
| Protection from Air, Fire, Water, Earth | damage let through: 70% / 70% / 50% / 50% → 50% / 50% / 25% / 25% (none / Basic / Advanced / Expert) |
| Summon Fire Elemental, Summon Earth Elemental | summoned per Spell Power 2 / 2 / 3 / 4 → 2 / 2 / 2 / 3 |

No change in mana costs, spell levels or per-spell AI values for the 70 hero spells.

## Hero classes

See [Heroes](../heroes/) for the 18 original classes.

The 18 original classes are unchanged: starting skills, primary skill chances, secondary skill weights and `Aggression` are identical. The table has six more rows: Captain, Navigator, Mercenary, Artificer, Chieftain, Elder.

## Creature banks

The SoD table and the generation rule are under [creature banks](../ai-neutral/#creature-banks).

| Bank | Change |
|---|---|
| Naga Bank, all levels | the resource part of the reward is gems instead of sulfur, same amounts |
| Dragon Fly Hive, all levels | upgrade chance for a guard stack 50% → 0% |

Guards, level chances and the other rewards of the 11 original banks are the same.

## New creature banks

Also from `HotA.dat` (`tools/hota_banks.py`) **[data]**. The twelve records `crbank21` to `crbank32` each hold a small plain-text block with the same fields as a row of `CRBANKS.TXT`: four levels with a chance, guard types and counts, an upgrade chance, and the reward.

Two things differ from the SoD table format:

- Guards are listed **stack by stack** (up to seven types and counts), so several banks name the same creature more than once. Whether HotA still applies the [SoD splitting rule](../ai-neutral/#creature-banks) to these lists is **[unverified]**.
- Each record starts with a "precise guard stack setup" flag. It is 1 only for Ruins; its effect is code in `HotA.dll` and was not read.

Churchyard has a single state (chance 100%, the other three 0%).

{% include banks.html lang="en" rows=site.data.hota_banks %}

## Battle AI code

What was checked, for the routines that choose a melee target and for the [bonus for drawing the retaliation](../ai-battle/#bonus-for-drawing-the-retaliation):

- **The code in `h3hota.exe` is the same.** The functions sit at shifted addresses, and apart from the addresses of the calls and globals inside them the bytes are identical to `Heroes3.exe`:

  | Routine | `Heroes3.exe` (this site) | `h3hota.exe` |
  |---|---|---|
  | Retreat check | `0x41e570` | `0x41e6f0` |
  | Bonus for drawing the retaliation | `0x41f3b0` | `0x41f530` |
  | Melee stack: target choice | `0x421680` | `0x421800` |
  | Trial exchange, attack value | `0x4359b0`, `0x435b90` | `0x435600`, `0x4357e0` |
  | Best hex to strike from | `0x436300` | `0x435f50` |
  | Unit value | `0x442a50` | `0x442770` |

- **`HotA.dll` hooks them, but for one purpose.** The library contains at least 36 small hook handlers that all call the same test (`HotA.dll` `0x10045990`) and then resume the original routine on one of its two existing branches. Six of them are inside the melee target routine, one is the first test of the retaliation bonus, and the rest are in the retreat check, the shooter and creature-spell routines, the hero spell evaluators and the morale code. The test is "is this stack out of action": HotA keeps its own table of effect durations for each stack and the test is true when any of **effects 62 (Blind), 70 (Stone Gaze), 74 (Paralyze) or 81** is active. Effect 81 has no row in the spell table of this build and was not identified.

  So everywhere the original AI asked "blinded, petrified or paralysed?", HotA asks the same question with one more disabling effect added. The scoring arithmetic, the random 75–100% factor, the ordering of targets and the retaliation bonus itself are not replaced by these handlers.

- **One special case for Couatls.** A handler in the melee target routine (`HotA.dll` `0x1004c260`) branches when the stack is a Couatl or Crimson Couatl (creatures 182, 183) with a flag set in its HotA data. What the flag means was not read.

Limits of this check: the handlers above were found because they contain plain return addresses. `HotA.dll` stores the addresses it hooks in scrambled form, so the list of hooks could not be enumerated, and a hook that replaces a whole routine or changes a value without returning into these functions would not show up this way. **[code `HotA.dll`; that the hooks found are all of them is unverified]**

## How this interacts with the rest of the site

Under the SoD rules described here, some of these numbers feed directly into decisions:

- Fight Value drives [battle AI](../ai-battle/#what-a-unit-is-worth) scoring; AI Value drives [join or flee](../ai-neutral/#before-the-fight-join-flee-or-fight) and [stack splitting](../ai-neutral/#how-the-stack-is-split-for-battle).
- A Dragon Fly Hive with a 0% upgrade chance never has an upgraded guard stack under the [bank generation](../ai-neutral/#creature-banks) rule.

Whether HotA keeps those rules is exactly the part that has not been checked.
