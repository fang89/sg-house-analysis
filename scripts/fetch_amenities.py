#!/usr/bin/env python3
"""Fetch + geocode all amenity layers -> data/amenities.json

Layers:
  ntuc / shengsiong   SFA supermarket licences (data/sfa_supermarkets.json),
                      postal extracted from premise address, geocoded via OneMap
  school              MOE School Directory (data/schools_raw.json),
                      PRIMARY + MIXED LEVEL (P1-S4), geocoded by postal
  mall                editorial list (data/malls.txt), geocoded by OneMap name search
  mrt                 LTA MRT/LRT Station Exits geojson (data/mrt_exits.geojson);
                      stations = mean of exit coords, exits kept for distance calc
  hawker              NEA hawker centres geojson (data/hawker_centres.geojson)
  extras              any data/extra_*.geojson dropped in by fetch_extras.py

OneMap is ~1 req/s; results cached in data/geocode_cache.json (resumable).
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CACHE_PATH = os.path.join(DATA, "geocode_cache.json")

SG_BOUNDS = (1.15, 1.48, 103.6, 104.1)


def load_cache():
    cache = {}
    seed = os.path.join(DATA, "geocode_cache_seed.json")
    if os.path.exists(seed):
        cache.update(json.load(open(seed)))
    if os.path.exists(CACHE_PATH):
        cache.update(json.load(open(CACHE_PATH)))
    return cache


CACHE = load_cache()


def onemap_search(term):
    """Return (lat, lon, matched_name) for a search term, cached."""
    if term in CACHE:
        v = CACHE[term]
        return tuple(v) if v else None
    url = ("https://www.onemap.gov.sg/api/common/elastic/search?"
           + urllib.parse.urlencode({"searchVal": term, "returnGeom": "Y",
                                     "getAddrDetails": "Y", "pageNum": 1}))
    for attempt in range(4):
        try:
            r = json.load(urllib.request.urlopen(url, timeout=15))
            results = r.get("results") or []
            if results:
                h = results[0]
                val = [float(h["LATITUDE"]), float(h["LONGITUDE"]),
                       h.get("SEARCHVAL", "")]
            else:
                val = None
            CACHE[term] = val
            time.sleep(0.9)
            return tuple(val) if val else None
        except Exception:
            time.sleep(3 * (attempt + 1))
    CACHE[term] = None
    return None


def save_cache():
    json.dump(CACHE, open(CACHE_PATH, "w"))


def in_sg(lat, lon):
    return SG_BOUNDS[0] < lat < SG_BOUNDS[1] and SG_BOUNDS[2] < lon < SG_BOUNDS[3]


def title(s):
    small = {"of", "the", "and", "at"}
    words = []
    for i, w in enumerate(re.split(r"\s+", s.strip().lower())):
        if w.startswith("#"):
            words.append(w.upper())
        else:
            words.append(w if (w in small and i) else w.capitalize())
    return " ".join(words)


def fetch_supermarkets():
    raw = json.load(open(os.path.join(DATA, "sfa_supermarkets.json")))
    out = []
    for r in raw:
        name = (r.get("business_name") or "").upper()
        lic = (r.get("name_of_license") or "").upper()
        if "FAIRPRICE" in name or "NTUC" in name or "FAIRPRICE" in lic:
            chain = "ntuc"
        elif "SHENG SIONG" in name or "SHENG SIONG" in lic:
            chain = "shengsiong"
        else:
            continue
        addr = r.get("premise_address") or ""
        m = re.search(r"S\((\d{6})\)", addr)
        if not m:
            continue
        postal = m.group(1)
        g = onemap_search(postal)
        if not g or not in_sg(g[0], g[1]):
            # licence postal unknown to OneMap — fall back to the street address
            street = re.sub(r"#[\w-]+", "", addr.split(", S(")[0]).strip()
            g = onemap_search(street)
        if not g or not in_sg(g[0], g[1]):
            print(f"  MISS supermarket {postal} {addr[:50]}", flush=True)
            continue
        clean_addr = title(addr.split(", S(")[0])
        label = "FairPrice" if chain == "ntuc" else "Sheng Siong"
        out.append({"name": f"{label} — {clean_addr}", "addr": clean_addr,
                    "postal": postal, "lat": round(g[0], 6), "lon": round(g[1], 6),
                    "cat": chain})
    return out


def fetch_schools():
    raw = json.load(open(os.path.join(DATA, "schools_raw.json")))
    out = []
    for s in raw:
        level = (s.get("mainlevel_code") or "").upper()
        if level != "PRIMARY" and "P1" not in level:
            continue
        postal = (s.get("postal_code") or "").strip().zfill(6)
        g = onemap_search(postal)
        if not g or not in_sg(g[0], g[1]):
            print(f"  MISS school {s['school_name']} {postal}", flush=True)
            continue
        out.append({"name": title(s["school_name"]),
                    "addr": title(s.get("address", "")), "postal": postal,
                    "lat": round(g[0], 6), "lon": round(g[1], 6),
                    "cat": "school", "level": level})
    return out


def fetch_malls():
    out = []
    for name in open(os.path.join(DATA, "malls.txt")):
        name = name.strip()
        if not name:
            continue
        g = onemap_search(name)
        if not g or not in_sg(g[0], g[1]):
            print(f"  MISS mall {name}", flush=True)
            continue
        out.append({"name": name, "addr": g[2].title(), "postal": "",
                    "lat": round(g[0], 6), "lon": round(g[1], 6), "cat": "mall"})
    return out


def fetch_mrt():
    g = json.load(open(os.path.join(DATA, "mrt_exits.geojson")))
    stations, exits = {}, []
    for f in g["features"]:
        p = f["properties"]
        name = (p.get("STATION_NA") or "").strip()
        lon, lat = f["geometry"]["coordinates"][:2]
        if not name or not in_sg(lat, lon):
            continue
        kind = "lrt" if "LRT" in name else "mrt"
        exits.append({"name": title(name.replace(" MRT STATION", "").replace(" LRT STATION", "")),
                      "lat": round(lat, 6), "lon": round(lon, 6),
                      "cat": kind, "exit": p.get("EXIT_CODE", "")})
        stations.setdefault(name, []).append((lat, lon))
    st_out = []
    for name, pts in stations.items():
        lat = sum(p[0] for p in pts) / len(pts)
        lon = sum(p[1] for p in pts) / len(pts)
        kind = "lrt" if "LRT" in name else "mrt"
        st_out.append({"name": title(name.replace(" MRT STATION", "").replace(" LRT STATION", "")),
                       "lat": round(lat, 6), "lon": round(lon, 6),
                       "cat": kind, "exits": len(pts)})
    return st_out, exits


def parse_desc(html):
    """data.gov.sg KML-style Description: <th>KEY</th> <td>VALUE</td> table."""
    return {m.group(1).strip(): m.group(2).strip()
            for m in re.finditer(r"<th>([^<]+)</th>\s*<td>([^<]*)</td>", html or "")}


def geojson_points(path, name_keys, cat, keep=None):
    """Extract point features (or polygon centroids) from a data.gov.sg geojson."""
    g = json.load(open(path))
    out = []
    for f in g["features"]:
        p = dict(f.get("properties") or {})
        p.update(parse_desc(p.get("Description", "")))
        if keep and not keep(p):
            continue
        name = ""
        for k in name_keys:
            if p.get(k):
                name = str(p[k]).strip()
                break
        geom = f["geometry"]
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"][:2]
        elif geom["type"] in ("Polygon", "MultiPolygon"):
            ring = (geom["coordinates"][0] if geom["type"] == "Polygon"
                    else geom["coordinates"][0][0])
            lon = sum(c[0] for c in ring) / len(ring)
            lat = sum(c[1] for c in ring) / len(ring)
        else:
            continue
        if not in_sg(lat, lon):
            continue
        out.append({"name": title(name) if name.isupper() else name,
                    "lat": round(lat, 6), "lon": round(lon, 6), "cat": cat})
    return out


def main():
    result = {}
    print("MRT/LRT stations…", flush=True)
    stations, exits = fetch_mrt()
    result["stations"] = stations
    result["station_exits"] = exits
    print(f"  {len(stations)} stations, {len(exits)} exits", flush=True)

    print("Hawker centres…", flush=True)
    result["hawker"] = geojson_points(
        os.path.join(DATA, "hawker_centres.geojson"),
        ["NAME", "ADDRESSBUILDINGNAME"], "hawker")
    print(f"  {len(result['hawker'])}", flush=True)

    # (category, name-key preference, row filter)
    EXTRAS = {
        "communityclub": (["NAME", "ADDRESSBUILDINGNAME", "DESCRIPTION"], None),
        # CHAS: medical clinics only (drop dental / pharmacy licences)
        "clinic": (["HCI_NAME", "NAME"],
                   lambda p: p.get("LICENCE_TYPE", "MC").upper() == "MC"),
    }
    for path in sorted(os.listdir(DATA)):
        if path.startswith("extra_") and path.endswith(".geojson"):
            cat = path[len("extra_"):-len(".geojson")]
            keys, keep = EXTRAS.get(cat, (["NAME"], None))
            result[cat] = geojson_points(os.path.join(DATA, path), keys, cat, keep)
            print(f"  extra {cat}: {len(result[cat])}", flush=True)

    print("Supermarkets…", flush=True)
    supers = fetch_supermarkets()
    save_cache()
    result["ntuc"] = [s for s in supers if s["cat"] == "ntuc"]
    result["shengsiong"] = [s for s in supers if s["cat"] == "shengsiong"]
    print(f"  {len(result['ntuc'])} FairPrice, {len(result['shengsiong'])} Sheng Siong", flush=True)

    print("Primary schools…", flush=True)
    result["school"] = fetch_schools()
    save_cache()
    print(f"  {len(result['school'])}", flush=True)

    print("Malls…", flush=True)
    result["mall"] = fetch_malls()
    save_cache()
    print(f"  {len(result['mall'])}", flush=True)

    json.dump(result, open(os.path.join(DATA, "amenities.json"), "w"))
    print("wrote data/amenities.json", flush=True)


if __name__ == "__main__":
    main()
