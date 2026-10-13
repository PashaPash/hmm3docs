---
title: Artifacts
parent: English
nav_order: 6.5
lang: en
---

# Artifacts

The 129 artifacts of `ARTRAITS.TXT` **[data]**: engine number, slot, class and gold price. The effect texts are not reproduced, and what each artifact does is code, not table data. The last column is what the computer player thinks the artifact is worth, read from the evaluator table in the executable **[data `0x63ac7c`]**; the symbols are explained under [artifact effect terms](../ai-adventure/#artifact-effect-terms).

Artifact numbers are how the rest of this site refers to them, for example 83 (Recanter's Cloak), 125 (Shackles of War), 126 (Orb of Inhibition) in the [battle AI](../ai-battle/), 137-style combination items in [damage](../combat/#hero-skills-in-the-formula), and 70, 72, 90, 98 in [hero movement](../adventure/).

## How these numbers are used

- **Class** decides where an artifact can turn up: [creature banks](../ai-neutral/#creature-banks), Pandora's Boxes and random map artifacts draw by class, and so does the weekly stock of merchants.
- **Price** is the gold price at merchants and the Black Market, before the Marketplace exchange rate.
- The **computer does not value an artifact by its price**. It uses the per-hero terms of the "AI value" column, see [what an artifact is worth](../ai-adventure/#what-an-artifact-is-worth). The price appears in AI code only as a floor: in the [retreat check](../ai-battle/#retreat) each artifact a hero carries counts for at least half its price.
- Combination artifacts (Angelic Alliance and the others) are not rows of this table in the Shadow of Death data; they are defined in the executable and listed [below](#combination-artifacts).

> **HotA 1.8.1:** the Ballista costs 1500 instead of 2500, and the table is extended with combination and new artifacts in a different column layout that was not compared row by row. See [HotA differences](../hota/).

{% include artifacts.html lang="en" %}

## Combination artifacts

The twelve combinations and their parts are built by code at `0x44c960` **[code]**; they have no rows in `ARTRAITS.TXT` of this build, so slot and price are not listed. A part that belongs to a combination is valued by the computer with the combination's terms added to its own.

{% include artifact_combos.html lang="en" %}
