#!/usr/bin/env python3
"""Nearest-amenity distance for every HDB block -> docs/data/*.json

Inputs:
  data/hdb_blocks_base.json  [[postal, blk, lat, lon, street, town, units], ...]
  data/amenities.json        {category: [{name, lat, lon, ...}]}

Outputs:
  docs/data/blocks.json     [[postal, blk, lat, lon, street, town, units,
                              d_L1, i_L1, d_L2, i_L2, ...], ...]
                            (d = metres to nearest, i = index into that layer's
                             point list in amenities.json)
  docs/data/amenities.json  {layers:{L:[[name,lat,lon,sub],...]},
                             stations:[[name,lat,lon,kind,n_exits],...]}
  docs/data/summary.json    headline stats per layer
"""
import json
import math
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs", "data")
os.makedirs(OUT, exist_ok=True)

M_PER_DEG_LAT = 110574.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(1.352))

# layer -> (amenities.json source keys merged in order, benchmark metres)
# benchmark = walkability yardstick used for gap coloring (user-adjustable in UI)
LAYERS = [
    ("mrt",    ["stations"],           800),   # station (mean of exits)
    ("super",  ["ntuc", "shengsiong"], 500),
    ("infantcare", ["infantcare"],     800),
    ("school", ["school"],             1000),
    ("mall",   ["mall"],               1000),
    ("hawker", ["hawker"],             500),
    ("communityclub", ["communityclub"], 1000),
]

# Rent-affordability points: block's average rent vs the island-wide
# average for the same flat types (so a 3-room block isn't "cheap" just
# for being small). <=RENT_CHEAP of island average = 2 pts, <=RENT_MID =
# 1 pt, above = 0. Blocks with <RENT_MIN_N rentals fall back to their
# town's ratio; no data at all = neutral 1 pt.
RENT_CHEAP, RENT_MID, RENT_MIN_N = 0.95, 1.10, 3

# HDB town code -> rental dataset town name
TOWN_NAME = {
    "AMK": "ANG MO KIO", "BB": "BUKIT BATOK", "BD": "BEDOK", "BH": "BISHAN",
    "BM": "BUKIT MERAH", "BP": "BUKIT PANJANG", "BT": "BUKIT TIMAH",
    "CCK": "CHOA CHU KANG", "CL": "CLEMENTI", "CT": "CENTRAL AREA",
    "GL": "GEYLANG", "HG": "HOUGANG", "JE": "JURONG EAST",
    "JW": "JURONG WEST", "KWN": "KALLANG/WHAMPOA", "MP": "MARINE PARADE",
    "PG": "PUNGGOL", "PRC": "PASIR RIS", "QT": "QUEENSTOWN",
    "SB": "SEMBAWANG", "SGN": "SERANGOON", "SK": "SENGKANG",
    "TAP": "TAMPINES", "TG": "TENGAH", "TP": "TOA PAYOH",
    "WL": "WOODLANDS", "YS": "YISHUN",
}


def dist_m(lat1, lon1, lat2, lon2):
    dy = (lat1 - lat2) * M_PER_DEG_LAT
    dx = (lon1 - lon2) * M_PER_DEG_LON
    return math.hypot(dx, dy)


class Grid:
    CELL = 0.0063  # ~700 m

    def __init__(self, pts):
        self.pts = pts
        self.cells = defaultdict(list)
        for i, (lat, lon) in enumerate(pts):
            self.cells[(int(lat / self.CELL), int(lon / self.CELL))].append(i)

    def nearest(self, lat, lon):
        ci, cj = int(lat / self.CELL), int(lon / self.CELL)
        best, best_i = float("inf"), -1
        ring = 0
        while True:
            for i in range(ci - ring, ci + ring + 1):
                for j in range(cj - ring, cj + ring + 1):
                    if ring and max(abs(i - ci), abs(j - cj)) < ring:
                        continue
                    for k in self.cells.get((i, j), ()):
                        d = dist_m(lat, lon, *self.pts[k])
                        if d < best:
                            best, best_i = d, k
            if best_i >= 0 and ring * self.CELL * M_PER_DEG_LAT > best + 700:
                return best, best_i
            ring += 1
            if ring > 80:
                return best, best_i


def norm_street(s):
    return " ".join((s or "").upper().split())


def load_rents():
    """(street, blk) and town rent stats from the last 12 months of HDB
    rental approvals, normalized by flat type."""
    path = os.path.join(DATA, "rents.json")
    if not os.path.exists(path):
        return None
    rows = json.load(open(path))
    by_ft = defaultdict(list)
    for _, _, _, _, ft, rent in rows:
        by_ft[ft].append(rent)
    ft_avg = {ft: sum(v) / len(v) for ft, v in by_ft.items()}
    blocks = defaultdict(lambda: [0, 0.0, 0.0])   # n, sum(rent), sum(ratio)
    towns = defaultdict(lambda: [0, 0.0, 0.0])
    for _, town, blk, street, ft, rent in rows:
        ratio = rent / ft_avg[ft]
        b = blocks[(norm_street(street), blk)]
        t = towns[town]
        for agg in (b, t):
            agg[0] += 1
            agg[1] += rent
            agg[2] += ratio
    return blocks, towns, ft_avg


def rent_points(ratio):
    return 2 if ratio <= RENT_CHEAP else 1 if ratio <= RENT_MID else 0


def sub_of(p):
    c = p.get("cat", "")
    if c in ("ntuc", "shengsiong", "mrt", "lrt"):
        return c
    return ""


def main():
    blocks = json.load(open(os.path.join(DATA, "hdb_blocks_base.json")))
    amen = json.load(open(os.path.join(DATA, "amenities.json")))

    grids, layer_pts = {}, {}
    for name, keys, _ in LAYERS:
        pts = [p for k in keys for p in amen.get(k, [])]
        layer_pts[name] = pts
        grids[name] = Grid([(p["lat"], p["lon"]) for p in pts])
        print(f"{name}: {len(pts)} points")

    rents = load_rents()
    rent_hits = 0
    out_blocks = []
    dists = defaultdict(list)
    for postal, blk, lat, lon, street, town, units in blocks:
        row = [postal, blk, lat, lon, street, town, units]
        for name, _, _ in LAYERS:
            d, i = grids[name].nearest(lat, lon)
            row += [round(d), i]
            dists[name].append(round(d))
        # rent: [avg S$/mo shown, n block rentals (0 = town average), pts]
        if rents:
            rb, rt, _ = rents
            n, s, r = rb.get((norm_street(street), blk.upper()), (0, 0, 0))
            tn, ts, tr = rt.get(TOWN_NAME.get(town, ""), (0, 0, 0))
            if n:
                rent_hits += 1
            if n >= RENT_MIN_N:
                row += [round(s / n), n, rent_points(r / n)]
            elif n:      # too few to score on, but real block data to show
                row += [round(s / n), n,
                        rent_points(tr / tn) if tn else 1]
            elif tn:
                row += [round(ts / tn), 0, rent_points(tr / tn)]
            else:
                row += [0, 0, 1]
        else:
            row += [0, 0, 1]
        out_blocks.append(row)

    n = len(out_blocks)
    summary = {
        "generated": __import__("datetime").date.today().isoformat(),
        "blocks": n,
        "layer_order": [name for name, _, _ in LAYERS],
        "benchmarks": {name: bench for name, _, bench in LAYERS},
        "layers": {},
    }
    for name, _, bench in LAYERS:
        ds = sorted(dists[name])
        summary["layers"][name] = {
            "count": len(layer_pts[name]),
            "benchmark_m": bench,
            "median_m": ds[n // 2],
            "p90_m": ds[int(n * 0.9)],
            "max_m": ds[-1],
            "blocks_over": sum(1 for d in ds if d > bench),
            "pct_within": round(100 * sum(1 for d in ds if d <= bench) / n, 1),
        }
    # stations are display-only (distance uses exits); count them for the tiles
    summary["stations"] = {
        "mrt": sum(1 for s in amen.get("stations", []) if s["cat"] == "mrt"),
        "lrt": sum(1 for s in amen.get("stations", []) if s["cat"] == "lrt"),
    }
    if rents:
        _, _, ft_avg = rents
        shown = [b[-3] for b in out_blocks if b[-3] > 0]
        summary["rent"] = {
            "months": 12,
            "island_avg_by_flat_type": {k: round(v) for k, v in
                                        sorted(ft_avg.items())},
            "blocks_with_own_rentals": rent_hits,
            "pct_blocks_matched": round(100 * rent_hits / n, 1),
            "median_shown_avg": sorted(shown)[len(shown) // 2] if shown else 0,
            "bands": {"cheap": RENT_CHEAP, "mid": RENT_MID,
                      "min_n": RENT_MIN_N},
        }
        print(f"rent: {rent_hits} blocks matched own rentals "
              f"({summary['rent']['pct_blocks_matched']}%)")

    display = {
        "layers": {name: [[p["name"], p["lat"], p["lon"], sub_of(p)]
                          for p in layer_pts[name]]
                   for name, _, _ in LAYERS},
        "stations": [[s["name"], s["lat"], s["lon"], s["cat"], s["exits"]]
                     for s in amen.get("stations", [])],
    }
    json.dump(out_blocks, open(os.path.join(OUT, "blocks.json"), "w"),
              separators=(",", ":"))
    json.dump(display, open(os.path.join(OUT, "amenities.json"), "w"),
              separators=(",", ":"))
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
