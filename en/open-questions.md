---
title: Open questions
parent: English
nav_order: 15
lang: en
---

# Open questions

Things referenced in the chapters but not decoded or not confirmed yet.

## Battle AI

- Hero spells: the evaluators are described from decompiled code without the exact floating-point expressions.

## Adventure map AI

- What the turn loop does with a hero standing in one of the player's towns once no hero has movement left (`0x526a90`, `0x5be390`): the code moves a visiting hero into the garrison; the purpose was not traced.

## Everything else

Chapter 14 covers only table differences, not HotA's code or new towns; chapter 2 has building tables only; chapter 7 has only hero movement. See the progress table on the [home page]({{ '/' | relative_url }}).

## Build note

Data addresses in this executable are 0x50 lower than the ones commonly quoted by the modding community for some globals (for example the combat manager pointer is at `0x6993d0` here). Always check the SHA-256 on the [method page](../method/) before reusing addresses.
