#!/usr/bin/env python3
"""Turn the game's text tables (dumped by lod.py) into _data/*.json.

Usage: extract_tables.py <dir with *.TXT> <_data dir>

Only numbers and identifiers are written. Description texts are dropped.
"""
import csv
import io
import json
import sys
from pathlib import Path

RES = ["wood", "mercury", "ore", "sulfur", "crystal", "gems", "gold"]
TOWNS = ["castle", "rampart", "tower", "inferno", "necropolis", "dungeon",
         "stronghold", "fortress", "conflux"]
# Conflux creature ids are not contiguous; (level, upgraded) by id.
CONFLUX = {118: (1, 0), 119: (1, 1), 112: (2, 0), 127: (2, 1), 115: (3, 0),
           123: (3, 1), 114: (4, 0), 129: (4, 1), 113: (5, 0), 125: (5, 1),
           120: (6, 0), 121: (6, 1), 130: (7, 0), 131: (7, 1)}


def rows(src, name):
    text = (src / f"{name}.TXT").read_bytes().decode("cp1252")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return list(csv.reader(io.StringIO(text), delimiter="\t"))


def num(s):
    s = s.strip().rstrip("%")
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return 0


def creatures(src):
    out = []
    for r in rows(src, "CRTRAITS")[2:]:
        if len(r) < 25 or not r[9].strip().isdigit():
            continue
        cid = len(out)
        town, level, upg = None, None, None
        if cid < 112:
            town, level, upg = TOWNS[cid // 14], cid % 14 // 2 + 1, cid % 2
        elif cid in CONFLUX:
            town, (level, upg) = "conflux", CONFLUX[cid]
        n = [num(c) for c in r[2:23]]
        out.append({
            "id": cid, "name": r[0].strip(), "plural": r[1].strip(),
            "town": town, "level": level, "upgraded": upg,
            "cost": {k: v for k, v in zip(RES, n[0:7]) if v},
            "fight_value": n[7], "ai_value": n[8], "growth": n[9],
            "horde_growth": n[10], "hp": n[11], "speed": n[12],
            "attack": n[13], "defense": n[14], "dmg_min": n[15],
            "dmg_max": n[16], "shots": n[17], "spells": n[18],
            "map_min": n[19], "map_max": n[20],
            "flags": [f.strip() for f in r[24].split("|") if f.strip() not in ("", "0")],
        })
    return out


def hero_classes(src):
    r = rows(src, "HCTRAITS")
    head = next(x for x in r if x and x[0] == "Name")
    skills = [h.strip() for h in head[14:42]]
    out = []
    for x in r[r.index(head) + 1:]:
        if len(x) < 51 or not x[0].strip():
            continue
        n = [num(c) for c in x[2:51]]
        out.append({
            "id": len(out), "name": x[0].strip(),
            "town": TOWNS[len(out) // 2] if len(out) // 2 < len(TOWNS) else None,
            "aggression": num(x[1]),
            "start": n[0:4], "gain_low": n[4:8], "gain_high": n[8:12],
            "skill_weights": dict(zip(skills, n[12:40])),
            "tavern_weights": dict(zip(TOWNS, n[40:49])),
        })
    return out


def heroes(src):
    out = []
    for x in rows(src, "HOTRAITS")[2:]:
        if len(x) < 10 or not x[1].strip().isdigit():
            continue
        out.append({"id": len(out), "name": x[0].strip(), "army": [
            {"creature": x[i + 2].strip(), "min": num(x[i]), "max": num(x[i + 1])}
            for i in (1, 4, 7)]})
    return out


def spells(src):
    out, kind = [], None
    for x in rows(src, "SPTRAITS")[2:]:
        if len(x) < 29:
            continue
        if not x[2].strip().isdigit():
            if x[0].strip():
                kind = x[0].split()[0].lower()
            continue
        n = [num(c) for c in x[2:29]]
        out.append({
            "id": len(out), "name": x[0].strip(), "kind": kind, "level": n[0],
            "schools": [s for s, c in zip(["earth", "water", "fire", "air"], x[3:7]) if c.strip()],
            "cost": n[5:9], "power": n[9], "effect": n[10:14],
            "town_chance": dict(zip(TOWNS, n[14:23])), "ai_value": n[23:27],
            "flags": [f.strip() for f in x[33].split("|") if f.strip()] if len(x) > 33 else [],
        })
    return out


def artifacts(src):
    r = rows(src, "ARTRAITS")
    slots = [s.strip() for s in r[1][2:20]]
    out = []
    for x in r[2:]:
        if len(x) < 21 or not x[0].strip():
            continue
        out.append({"id": len(out), "name": x[0].strip(), "cost": num(x[1]),
                    "slots": [s for s, c in zip(slots, x[2:20]) if c.strip()],
                    "class": x[20].strip()})
    return out


def banks(src):
    out, name = [], None
    for x in rows(src, "CRBANKS")[2:]:
        if len(x) < 27 or not x[1].strip().isdigit():
            continue
        name = x[0].strip() or name
        guards = [{"count": num(x[3]), "creature": x[4].strip()}]
        guards += [{"count": num(x[i]), "creature": x[i + 1].strip()}
                   for i in (6, 8, 10) if num(x[i])]
        out.append({
            "bank": name, "level": num(x[1]), "chance": num(x[2]),
            "guards": guards, "upgrade_chance": num(x[5]),
            "combat_value": num(x[12]),
            "resources": {k: num(v) for k, v in zip(RES, x[13:20]) if num(v)},
            "creatures": {"count": num(x[20]), "creature": x[21].strip()} if num(x[20]) else None,
            "artifacts": dict(zip(["treasure", "minor", "major", "relic"], [num(c) for c in x[22:26]])),
            "value": num(x[26]),
        })
    return out


def movement(src):
    r = rows(src, "MOVEMENT")[2:]
    return {
        "land_by_slowest_speed": [num(x[1]) for x in r if x and x[0].strip().isdigit()],
        "sea_by_navigation": [num(x[3]) for x in r if len(x) > 3 and x[3].strip().isdigit()],
        "bonuses": {x[4].strip(): num(x[5]) for x in r if len(x) > 5 and x[4].strip()},
    }


def ballistics(src):
    keys = ["keep", "tower", "gate", "wall", "shots", "dmg0", "dmg1", "dmg2"]
    return [dict(zip(keys, [num(c) for c in x[2:10]]), level=x[1].strip())
            for x in rows(src, "BALLIST")[2:] if len(x) > 9]


def buildings(src):
    out, section, town = [], None, None
    for x in rows(src, "BUILDING")[1:]:
        if len(x) < 8:
            continue
        if not x[6].strip().isdigit():
            label = x[0].strip()
            if label.lower() in TOWNS:
                town = label.lower()
            elif label:
                section, town = label, None
            continue
        cost = {k: num(v) for k, v in zip(RES, x[0:7]) if num(v)}
        if x[7].strip():
            out.append({"section": section, "town": town, "name": x[7].strip(), "cost": cost})
    return out


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    tables = {"creatures": creatures, "hero_classes": hero_classes, "heroes": heroes,
              "spells": spells, "artifacts": artifacts, "creature_banks": banks,
              "movement": movement, "ballistics": ballistics, "buildings": buildings}
    for name, fn in tables.items():
        data = fn(src)
        (dst / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
        print(name, len(data))


if __name__ == "__main__":
    main()
