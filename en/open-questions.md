---
title: Open questions
parent: English
nav_order: 15
lang: en
---

# Open questions

Things referenced in the chapters but not decoded or not confirmed yet.

## Battle AI

- Hero spells: the evaluators are described from decompiled code without the exact floating-point expressions; the meaning of spell flag `0x4000` is not identified.
- Exact strength terms in the retreat check (`0x41e570`): a multiplier for stacks that have not acted, the defender's bonus inside a town, and the role of the gold comparison.
- The meaning of the per-game field at `+0x1f698` that enables moat awareness and changes sympathy for elementals. It looks like the map's expansion level. **[inferred]**
- Quick combat.

## Neutral monsters

- Stack splitting: the two extra hero-side calls before the strength ratio in `0x4ac580`, and battlefield placement.
- Creature banks: where the guard stacks stand on the battlefield; how the computer player decides whether a bank is worth attacking (`0x52bd10`).
- Bounds of random stack sizes at map start and in a creature month.

## Adventure map AI

- What the turn loop does with a hero standing in one of the player's towns once no hero has movement left (`0x526a90`, `0x5be390`): the code moves a visiting hero into the garrison; the purpose was not traced.

## Everything else

Chapter 14 covers only table differences, not HotA's code or new towns; chapter 2 has building tables only; chapter 7 has only hero movement. Town AI gaps are listed at the end of [AI: towns](../ai-towns/#not-decoded-yet). See the progress table on the [home page]({{ '/' | relative_url }}).

## Build note

Data addresses in this executable are 0x50 lower than the ones commonly quoted by the modding community for some globals (for example the combat manager pointer is at `0x6993d0` here). Always check the SHA-256 on the [method page](../method/) before reusing addresses.
