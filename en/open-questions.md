---
title: Open questions
parent: English
nav_order: 15
lang: en
---

# Open questions

Things referenced in the chapters but not decoded or not confirmed yet.

## Battle AI

- Hero spell selection: `0x43c800` and the evaluator class with vtable `0x63b7d8` (about 4,000 lines of decompiled code in `0x435e00`–`0x43d000`).
- The random factor applied to melee target scores in `0x421680`: its range.
- Exact strength terms in the retreat check (`0x41e570`): a multiplier for stacks that have not acted, the defender's bonus inside a town, and the role of the gold comparison.
- The per-hero defence factor `0x4e4310` used in unit valuation.
- The meaning of the per-game field at `+0x1f698` that enables moat awareness and changes sympathy for elementals. It looks like the map's expansion level. **[inferred]**
- Confirmation that `0x617b94` is a square root.
- Quick combat.

## Neutral monsters

- Translation of the map's disposition setting into the aggression number.
- Splitting of a map stack into battlefield stacks.
- Creature banks: level roll, guard placement.
- Weekly growth.

## Everything else

Chapters 2, 5, 7, 9, 10, 11 and 14 are not started. See the progress table on the [home page]({{ '/' | relative_url }}).

## Build note

Data addresses in this executable are 0x50 lower than the ones commonly quoted by the modding community for some globals (for example the combat manager pointer is at `0x6993d0` here). Always check the SHA-256 on the [method page](../method/) before reusing addresses.
