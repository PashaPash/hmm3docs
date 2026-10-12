#!/usr/bin/env python3
"""Read creature records from HotA.dat into JSON.

Usage: hota_dat.py <HotA.dat> <out.json>

HotA.dat ("HDAT") is a list of named records. Records named monstNNN describe
creature NNN: four length-prefixed strings (sound prefix, def file, singular,
plural), then a marker byte, the size 0x74 and a 0x74-byte image of the
engine's creature structure. Only numbers and names are kept.
"""
import json
import re
import struct
import sys

RES = ["wood", "mercury", "ore", "sulfur", "crystal", "gems", "gold"]
FIELDS = ["fight_value", "ai_value", "growth", "horde_growth", "hp", "speed", "attack",
          "defense", "dmg_min", "dmg_max", "shots", "spells", "map_min", "map_max"]


def lstr(d, o):
    n = struct.unpack_from("<I", d, o)[0]
    return d[o + 4:o + 4 + n].decode("cp1252"), o + 4 + n


def main():
    d = open(sys.argv[1], "rb").read()
    assert d[:4] == b"HDAT"
    out = []
    for m in re.finditer(rb"\x00\x00\x00monst(\d+)", d):
        cid = int(m.group(1))
        o = m.start() + 3 + len(m.group(0)) - 3
        _, o = lstr(d, o)          # path
        o += 8
        strings = []
        for _ in range(4):
            s, o = lstr(d, o)
            strings.append(s)
        k = d.find(b"\x01\x74\x00\x00\x00", o, o + 64)
        if k < 0:
            continue
        rec = d[k + 5:k + 5 + 0x74]
        town, level = struct.unpack_from("<2i", rec, 0)
        flags = struct.unpack_from("<I", rec, 0x10)[0]
        cost = struct.unpack_from("<7i", rec, 0x20)
        vals = struct.unpack_from("<14i", rec, 0x3C)
        row = {"id": cid, "name": strings[2], "plural": strings[3], "town": town,
               "level": level + 1, "flags": flags,
               "cost": {r: c for r, c in zip(RES, cost) if c}}
        row.update(zip(FIELDS, vals))
        out.append(row)
    out.sort(key=lambda r: r["id"])
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    for r in out:
        print(r["id"], r["name"], "town", r["town"], "lv", r["level"], "A", r["attack"], "D", r["defense"],
              "dmg", r["dmg_min"], r["dmg_max"], "hp", r["hp"], "spd", r["speed"], "gr", r["growth"],
              "gold", r["cost"].get("gold"), "FV", r["fight_value"], "AI", r["ai_value"], hex(r["flags"]))


if __name__ == "__main__":
    main()
