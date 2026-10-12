---
title: Combat rules
parent: English
nav_order: 5
lang: en
---

# Combat rules
{: .no_toc }

First section only: the damage formula. Turn order, morale, luck rolls, retaliation and siege rules are not written yet.

1. TOC
{:toc}

## Damage

`0x443f40` computes the damage of one attack. `base` is the stack's rolled damage (per-creature roll times count; Bless and Curse replace the roll with the maximum or minimum).

```
damage = (base + bonus) × reduction × defending hero's factor        at least 1
```

### Bonus

`0x443320` and `0x443840`. Every item is a fraction of `base`, and the items are **added together**.

| Source | Bonus |
|---|---|
| Attack above the target's Defence | +5% per point, at most +300% |
| Lucky strike (stack flag set for this attack) | +100% **[flag meaning inferred]** |
| Cavalier, Champion charging | +5% per hex travelled; none against Pikemen and Halberdiers |
| Opposed elementals: Air or Storm against Earth or Magma and the reverse; Fire or Energy against Water or Ice and the reverse | +100% |
| Hated enemy: Angels and Devils, Genies and Efreet, Titans and Black Dragons, each way, including upgrades | +50% |
| Dread Knight | 20% chance of +100% |
| Ballista | +100% with a chance by the hero's Artillery level: none 0%, Basic 50%, Advanced 75%, Expert 100% (table `0x63b810`) |
| Attacking hero's Offence (melee) or Archery (ranged), Bless specialist | Added here by `0x4e42b0` / `0x4e4160`; exact terms not read yet |

"Attack" and "Defence" are the stacks' current values: creature stats, hero primary skills and spell effects. Moat hexes lower the defender's Defence by 3 (`0x442590`).

### Reduction

`0x443b90`. These **multiply**.

| Condition | Factor |
|---|---|
| Target's Defence above the Attack | `1 − 0.025` per point, not below 0.3 |
| Ranged attack beyond full range | 0.5 |
| Ranged attack through walls | 0.5 |
| A shooter fighting in melee, unless it has the "no melee penalty" flag | 0.5 |
| Psychic Elemental attacking a creature immune to mind spells | 0.5 |
| Magic Elemental attacking a Magic Elemental or a Black Dragon | 0.5 |
| Two more factors tied to spell effects on the attacker | not decoded |

The defending hero's factor (`0x4e4310`, Armorer) is applied last; its exact form is not read yet. Shield and Air Shield are applied as stored per-stack factors.

### Two asymmetries worth noticing

- Attack advantage is worth 5% per point but Defence advantage only 2.5% per point.
- The attack bonus is capped at +300% (60 points of difference), the defence reduction at −70% (28 points).

**[code; constants at `0x63ac58`, `0x63ac28`, `0x63b8c0`, `0x63b8b8`, `0x63ac70`]**
