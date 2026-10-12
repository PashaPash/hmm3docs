---
title: Method and evidence
parent: English
nav_order: 1
lang: en
---

# Method and evidence

## What was analysed

| File | Role | SHA-256 |
|---|---|---|
| `Heroes3.exe` | Game executable, GOG Heroes III Complete (Shadow of Death 3.2 engine). Image base `0x400000`, about 13,300 functions. | `057c9d88e7206f6669a4615de2c6e02ab6c4e2d570a9e2badf07fe0bd6247274` |
| `H3bitmap.lod`, `H3ab_bmp.lod` | Archives holding the text tables the engine reads at start-up (`CRTRAITS.TXT`, `HCTRAITS.TXT`, `SPTRAITS.TXT`, `CRBANKS.TXT`, …) | |
| `HotA.dll`, `HotA.dat` | Horn of the Abyss 1.8.1, used only for the chapter on HotA differences | |

The executable has no symbols. Function and field names used in these pages are ours. Addresses are virtual addresses in the unmodified `Heroes3.exe`, so anyone with the same file can open the same place in a disassembler.

Tools: Ghidra 12.1 for decompilation, small Python scripts for the archives. The scripts are in the [repository](https://github.com/PashaPash/hmm3docs/tree/main/tools). No game files are redistributed here.

## Evidence tags

| Tag | Meaning |
|---|---|
| **[code `0x…`]** | Read from the decompiled function at that address. |
| **[data `FILE.TXT`]** | Value taken from a game data table. |
| **[inferred]** | Follows from code or data that was read, but the exact path was not traced end to end. |
| **[unverified]** | Commonly stated about the game, not yet confirmed in the binary. |

Static analysis shows what the code does, not how often a branch is taken in real games. Where a rule was also checked in the running game, the page says so.

## Scope

The baseline is the unmodified Shadow of Death executable. HD mod and Horn of the Abyss change engine code in memory at run time; their behaviour is described only in the HotA chapter and only where it was confirmed.
