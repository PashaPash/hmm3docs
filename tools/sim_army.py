#!/usr/bin/env python3
"""Rate creatures and towns under the battle simulator's own arithmetic.

Usage: sim_army.py <_data dir>

Uses only what the AI battle page documents for battles without a battlefield:
pool = Fight Value x count; a shooter deals 20% of its strength per round from
round 1 (doubled with two shots); a walker or flyer deals 20% per round from
its arrival round, (speed + 14) // speed, capped at 4; three rounds in all.
No hero, no Tactics, no spells, gold cost only.
"""
import json
import sys
from pathlib import Path

TOWNS = ["castle", "rampart", "tower", "inferno", "necropolis", "dungeon",
         "stronghold", "fortress", "conflux"]


def rate(c):
    shooter = c["shots"] > 0
    arrival = 0 if shooter else min(4, (c["speed"] + 14) // c["speed"])
    if shooter:
        share = 0.6 * (2 if "const_two_attacks" in c["flags"] else 1)
    else:
        share = 0.2 * max(0, 4 - arrival)
    gold = c["cost"].get("gold", 0)
    return {
        "id": c["id"], "name": c["name"], "town": c["town"], "level": c["level"],
        "upgraded": c["upgraded"], "speed": c["speed"], "shooter": shooter,
        "arrival": arrival, "gold": gold, "fv": c["fight_value"], "growth": c["growth"],
        "extra_cost": sorted(k for k in c["cost"] if k != "gold"),
        "pool_per_1000": round(c["fight_value"] * 1000 / gold) if gold else 0,
        "share": round(share, 2),
        "output_per_1000": round(share * c["fight_value"] * 1000 / gold) if gold else 0,
    }


def main():
    data = Path(sys.argv[1])
    rows = [rate(c) for c in json.loads((data / "creatures.json").read_text())
            if c.get("town") in TOWNS and "NOT USED" not in c["name"]]
    towns = []
    for t in TOWNS:
        for up in (0, 1):
            cs = [r for r in rows if r["town"] == t and r["upgraded"] == up]
            gold = sum(r["gold"] * r["growth"] for r in cs)
            pool = sum(r["fv"] * r["growth"] for r in cs)
            out = sum(r["share"] * r["fv"] * r["growth"] for r in cs)
            towns.append({
                "town": t, "upgraded": up, "gold": gold, "pool": pool, "output": round(out),
                "output_share": round(100 * out / pool),
                "pool_per_1000": round(pool * 1000 / gold),
                "output_per_1000": round(out * 1000 / gold),
                "idle": [r["name"] for r in cs if r["share"] == 0],
            })
    best = sorted(rows, key=lambda r: -r["output_per_1000"])[:20]
    (data / "sim_army.json").write_text(json.dumps(
        {"creatures": rows, "towns": towns, "best": best}, indent=1) + "\n")
    for t in towns:
        print(t)
    for r in best:
        print(r["name"], r["town"], r["arrival"], r["share"], r["pool_per_1000"], r["output_per_1000"])


if __name__ == "__main__":
    main()
