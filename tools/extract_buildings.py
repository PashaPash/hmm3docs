#!/usr/bin/env python3
"""Town buildings: costs from BUILDING.TXT, names from BLDGSPEC.TXT and DWELLING.TXT,
prerequisites from the executable.

Usage: extract_buildings.py <dir with BUILDING.TXT> <Heroes3.exe> <_data dir>

The prerequisite lists are static int arrays in the executable, one per town
type, in the form: building, dep, dep, ..., -1, building, ..., -1, -1.
"""
import csv
import io
import json
import struct
import sys
from pathlib import Path

import peread

TOWNS = ["castle", "rampart", "tower", "inferno", "necropolis", "dungeon",
         "stronghold", "fortress", "conflux"]
RES = ["wood", "mercury", "ore", "sulfur", "crystal", "gems", "gold"]
COMMON = {0: "Mage Guild 1", 1: "Mage Guild 2", 2: "Mage Guild 3", 3: "Mage Guild 4",
          4: "Mage Guild 5", 5: "Tavern", 6: "Shipyard", 7: "Fort", 8: "Citadel",
          9: "Castle", 10: "Village Hall", 11: "Town Hall", 12: "City Hall",
          13: "Capitol", 14: "Marketplace", 15: "Resource Silo", 16: "Blacksmith",
          26: "Grail"}
DEPS_START = 0x63EC80


def sections(src):
    text = (src / "BUILDING.TXT").read_bytes().decode("cp1252")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out, cur = {}, None
    for row in list(csv.reader(io.StringIO(text), delimiter="\t"))[1:]:
        if len(row) < 8:
            continue
        if not row[6].strip().isdigit():
            label = row[0].strip()
            if label:
                cur = out.setdefault(label, [])
            continue
        cost = {k: int(v) for k, v in zip(RES, row[:7]) if v.strip() not in ("", "0")}
        cur.append((row[7].strip(), cost))
    return out


def names(src, fname):
    text = (src / fname).read_bytes().decode("cp1252")
    return [l.split("\t")[0].strip() for l in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def dep_lists(exe):
    data, secs = peread.load(exe)
    off = peread.offset(secs, DEPS_START)
    towns = []
    for _ in TOWNS:
        deps = {}
        while True:
            b = struct.unpack_from("<i", data, off)[0]
            off += 4
            if b < 0:
                break
            req = []
            while True:
                d = struct.unpack_from("<i", data, off)[0]
                off += 4
                if d < 0:
                    break
                req.append(d)
            deps[b] = req
        towns.append(deps)
    return towns, DEPS_START + off - peread.offset(secs, DEPS_START)


def main():
    src, exe, dst = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    sec = sections(src)
    keys = list(sec)
    print("sections:", [(k, len(v)) for k, v in sec.items()])
    deps, end = dep_lists(exe)
    print(f"dependency lists end at {end:#x}")
    # BUILDING.TXT layout: one "special" block of 9 rows per town (ids 17..25),
    # one neutral block of 17 rows (ids 0..16), one dwelling block of 14 rows
    # per town (ids 30..43).
    out = {}
    special = [k for k in keys if k.lower() in TOWNS][:9]
    for ti, town in enumerate(TOWNS):
        rows = {}
        for i, (name, cost) in enumerate(sec["Neutral Buildings"] if "Neutral Buildings" in sec else []):
            rows[i] = (COMMON.get(i, name), cost)
        for i, (name, cost) in enumerate(sec[special[ti]][:9]):
            rows[17 + i] = (name, cost)
        for i, (name, cost) in enumerate(sec[special[ti]][9:23]):
            rows[30 + i] = (name, cost)
        # In-game names: BLDGSPEC.TXT has 11 rows per town (ids 17..26, then the
        # Resource Silo), DWELLING.TXT has 14 rows per town (ids 30..43).
        for i, name in enumerate(names(src, "BLDGSPEC.TXT")[ti * 11:ti * 11 + 10]):
            if name and 17 + i in rows:
                up = " (upgraded creature)" if 17 + i in (19, 25) else ""
                rows[17 + i] = (name + up, rows[17 + i][1])
            elif name and 17 + i == 26:
                rows[26] = (name + " (Grail)", {})
        for i, name in enumerate(names(src, "DWELLING.TXT")[ti * 14:ti * 14 + 14]):
            if name and 30 + i in rows:
                rows[30 + i] = (name, rows[30 + i][1])
        common = dict(COMMON)
        common.pop(26)
        out[town] = [
            {"id": b, "name": common.get(b) or rows.get(b, ("", {}))[0],
             "cost": rows.get(b, ("", {}))[1], "requires": deps[ti].get(b, [])}
            for b in sorted(set(rows) | set(deps[ti]))
            if (common.get(b) or rows.get(b, ("", {}))[0]) and b in deps[ti]
        ]
    (dst / "town_buildings.json").write_text(json.dumps(out, indent=1) + "\n")
    for town in ("castle", "conflux"):
        print(town, [(b["id"], b["name"], b["requires"]) for b in out[town]][:60])


if __name__ == "__main__":
    main()
