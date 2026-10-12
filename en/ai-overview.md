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

### Battle behaviour

Difficulty switches parts of the battle logic on and off for every non-human side, including neutral monsters. See [AI: battle](../ai-battle/#what-difficulty-changes).

## Two value columns

`CRTRAITS.TXT` gives each creature two numbers ([table](../creatures/)):

- **Fight Value** is used inside battles to weigh damage dealt and taken.
- **AI Value** is used on the adventure map: army strength for the join/flee decision of wandering monsters is `Σ AI Value × count`, scaled by the hero's Attack and Defence. See [neutral monsters](../ai-neutral/).

Per-class `Aggression` from `HCTRAITS.TXT` and the per-spell AI values from `SPTRAITS.TXT` are read by adventure-map and spell-selection code that is not decoded yet.
