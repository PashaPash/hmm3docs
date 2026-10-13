#!/usr/bin/env python3
"""Dump the AI artifact evaluator table of Heroes3.exe (0x63ac7c) as short formulas.

Usage: artifact_ai.py <Heroes3.exe> <out.json>

The table is a list of: artifact id, then (evaluator type, arguments...) records
ended by -1; the whole list ends with a negative artifact id. The loader is at
0x4340e0. Symbols used in the formulas are explained on the AI adventure page.
"""
import json
import struct
import sys

from peread import load, offset

TABLE = 0x63AC7C
NARGS = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 2, 12: 1,
         13: 1, 14: 0, 15: 0, 16: 2, 17: 2, 18: 1, 19: 1, 20: 0, 21: 0, 22: 0, 23: 0}
SCHOOL = {1: "air", 2: "fire", 4: "water", 8: "earth"}
RES = ["wood", "mercury", "ore", "sulfur", "crystal", "gems", "gold"]
SPECIAL = {1: "scroll", 4: "ballista", 5: "Sh/40", 6: "tent"}


def term(t, a):
    n = a[0] if a else 0
    return {
        0: lambda: f"T×{n}/40",
        1: lambda: f"{n}×SP",
        2: lambda: f"{n}×K",
        3: lambda: f"M+{n}",
        4: lambda: f"L+{n}",
        5: lambda: f"Mv×{n}%",
        6: lambda: f"necro {n}",
        7: lambda: f"T×{n}%",
        8: lambda: f"(T+2500)×{n}%",
        9: lambda: f"T×{n}% [W]",
        10: lambda: f"{n}×D",
        11: lambda: f"orb({SCHOOL[n]})",
        12: lambda: f"tome({SCHOOL[n]})",
        13: lambda: "T/5 [−50×P]" if n == 0 else "T/8 [−25×P]",
        14: lambda: "M−enemy",
        15: lambda: "L−enemy",
        16: lambda: f"3×{n}×w({RES[a[1]]})",
        17: lambda: f"{a[1]}×AI(L{n + 1})",
        18: lambda: f"spell {n}",
        19: lambda: f"Sh×{n}%",
        20: lambda: "alliance",
        21: lambda: "necro 30",
        22: lambda: "living/8",
        23: lambda: "growth/2",
    }[t]()


def main():
    data, secs = load(sys.argv[1])
    p = offset(secs, TABLE)

    def nxt():
        nonlocal p
        v = struct.unpack_from("<i", data, p)[0]
        p += 4
        return v

    out = dict((str(k), v) for k, v in SPECIAL.items())
    while True:
        art = nxt()
        if art < 0:
            break
        terms = []
        while True:
            t = nxt()
            if t < 0:
                break
            terms.append(term(t, [nxt() for _ in range(NARGS[t])]))
        out[str(art)] = " + ".join(terms)
    json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=0, sort_keys=True)
    print(len(out), "artifacts")


if __name__ == "__main__":
    main()
