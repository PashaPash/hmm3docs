---
title: Open questions
parent: English
nav_order: 15
lang: en
---

# Open questions

Things referenced in the chapters but not decoded or not confirmed yet.

## Battle AI

- Hero spells: the evaluators not detailed in the battle chapter (most buffs and curses, Chain Lightning, Dispel, Resurrection, Sacrifice, Teleport), the meaning of spell flags `0x200` and `0x4000`, and battlefield type 2.
- Exact strength terms in the retreat check (`0x41e570`): a multiplier for stacks that have not acted, the defender's bonus inside a town, and the role of the gold comparison.
- The per-hero defence factor `0x4e4310` used in unit valuation.
- The meaning of the per-game field at `+0x1f698` that enables moat awareness and changes sympathy for elementals. It looks like the map's expansion level. **[inferred]**
- Confirmation that `0x617b94` is a square root.
- Quick combat.

## Neutral monsters

- Translation of the map's disposition setting into the aggression number.
- Stack splitting: the two extra hero-side calls before the strength ratio in `0x4ac580`, and battlefield placement.
- Creature banks: where the guard stacks stand on the battlefield; how the computer player decides whether a bank is worth attacking (`0x52bd10`).
- Bounds of random stack sizes at map start and in a creature month.

## Adventure map AI

See the list at the end of [AI: adventure map](../ai-adventure/#not-decoded-yet). The main obstacle is floating-point arithmetic that the decompiler drops; those functions need to be read as assembly.

## Everything else

Chapters 2, 5, 7, 9, 10 and 14 are not started. See the progress table on the [home page]({{ '/' | relative_url }}).

## Build note

Data addresses in this executable are 0x50 lower than the ones commonly quoted by the modding community for some globals (for example the combat manager pointer is at `0x6993d0` here). Always check the SHA-256 on the [method page](../method/) before reusing addresses.
