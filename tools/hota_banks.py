#!/usr/bin/env python3
"""Read creature bank records from HotA.dat into JSON.

Usage: hota_banks.py <HotA.dat> <_data dir>

Records named crbankNN contain the bank's name and a plain-text block with
four states: chance, guard types and counts, upgrade chance, resources,
artifacts by class, reward creature type and count.
"""
import json
import re
import struct
import sys
from pathlib import Path

RES = ["wood", "mercury", "ore", "sulfur", "crystal", "gems", "gold"]


def main():
    d = open(sys.argv[1], "rb").read()
    data = Path(sys.argv[2])
    names = {c["id"]: c["name"] for c in json.load(open(data / "creatures.json"))}
    names.update({c["id"]: c["name"] for c in json.load(open(data / "hota_creatures.json"))})
    out = []
    for m in re.finditer(rb"\x00\x00\x00(crbank(\d+))", d):
        o = m.start() + 3 + len(m.group(1))
        n = struct.unpack_from("<I", d, o)[0]          # path
        o += 4 + n + 8
        n = struct.unpack_from("<I", d, o)[0]
        bank = d[o + 4:o + 4 + n].decode("cp1252")
        k = d.find(b"# Precise guard stack setup", o)
        size = struct.unpack_from("<I", d, k - 4)[0]
        lines = [ln.split("#")[0].split() for ln in d[k:k + size].decode("cp1252").splitlines()]
        vals = [[int(x) for x in ln] for ln in lines if ln]
        precise, vals = vals[0][0], vals[1:]
        for level in range(4):
            chance, types, counts, upg, res, arts, ctype, ccount = vals[level * 8:level * 8 + 8]
            out.append({
                "id": int(m.group(2)), "bank": bank, "level": level + 1, "chance": chance[0],
                "precise": precise,
                "guards": [{"count": c, "creature": names.get(t, str(t))}
                           for t, c in zip(types, counts) if t >= 0 and c > 0],
                "upgrade_chance": upg[0],
                "resources": {r: v for r, v in zip(RES, res) if v},
                "artifacts": dict(zip(["treasure", "minor", "major", "relic"], arts)),
                "creatures": {"count": ccount[0], "creature": names.get(ctype[0], str(ctype[0]))}
                if ctype[0] >= 0 and ccount[0] > 0 else None,
            })
    json.dump(out, open(data / "hota_banks.json", "w"), indent=1)
    for b in out:
        if b["level"] in (1, 4):
            print(b["id"], b["bank"], b["level"], b["chance"], b["precise"], b["guards"], b["upgrade_chance"],
                  b["resources"], b["artifacts"], b["creatures"])


if __name__ == "__main__":
    main()
