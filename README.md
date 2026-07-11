# Which HDB block is the best in Singapore?

Interactive map scoring all ~13,400 HDB blocks **out of 10** on what daily
life there costs and how walkable it is. Weighted components, in priority
order:

| component | weight | data |
|---|---|---|
| Rent value | 2.0 | HDB rental approvals, last 12 months (41k transactions) |
| MRT / LRT station | 1.8 | 186 stations (mean of the LTA exit layer) |
| Hawker centre | 1.5 | 129, NEA |
| Supermarket (FairPrice / Sheng Siong) | 1.4 | 216 stores, SFA licence register |
| Shopping mall | 1.2 | 110 major malls, editorial list |
| Primary school | 1.0 | 182 schools, MOE School Directory |
| Infant care | 0.7 | 890 ECDA centres offering infant places |
| Community club | 0.4 | 130, PA |

Each amenity pays its full weight within its benchmark distance, half within
1.5x; rent pays full weight when the block rents at or below 0.95x the island
average for the same flat types (half up to 1.10x). Every block also displays
its **average monthly rent** (66% from the block's own transactions, the rest
the town average).

The dashboard opens on the score map (green = best). **Search a postal code /
address (OneMap) or click any block** for its full scorecard: per-component
points, every distance, average rent, how many of each amenity are nearby,
the runner-up option, and "between two stations" when that's the case. An
Explore mode, per-town filter, score histogram, best-towns ranking and a
top-50 table (residential blocks only) round it out.

**Live dashboard:** https://fang89.github.io/hdb-amenities/ *(after Pages is enabled)*

## Headline findings (2026-07-11)

- **65%** of HDB blocks are within 500 m of a FairPrice or Sheng Siong;
  4,662 blocks are beyond that (worst ≈ 3.3 km, in estates served mainly by
  other chains)
- **97%** are within 1 km of a primary school
- **72%** are within 800 m of an MRT/LRT station (median 550 m)
- Hawker centres are the scarcest headline amenity: median 640 m, only **39%**
  of blocks within 500 m
- Median score is **7.5/10**; 2,425 blocks score 9+. Tengah, Pasir Ris and
  Yishun average lowest (new estates where amenities are still building out)
- Median block-average rent is **S$3,200/mo**; island averages by flat type:
  3-room S$2,790, 4-room S$3,335, 5-room S$3,542

## Repo layout

```
scripts/fetch_amenities.py   # pull + geocode all amenity layers -> data/amenities.json
scripts/analyze.py           # nearest-amenity distance per block -> docs/data/*.json
data/                        # raw inputs & OneMap geocode cache
docs/                        # the static dashboard (publish this folder)
```

## Refresh the data

```bash
python3 scripts/fetch_amenities.py   # ~10 min first run (OneMap ~1 req/s), instant re-runs (cached)
python3 scripts/analyze.py           # rebuilds docs/data/{blocks,amenities,summary}.json
```

Raw inputs in `data/` and how to re-download them:

| file | source |
|---|---|
| `sfa_supermarkets.json` | [SFA supermarket licences](https://data.gov.sg/datasets?query=supermarkets) (data.gov.sg) |
| `schools_raw.json` | [MOE School Directory](https://data.gov.sg/datasets/d_688b934f82c1059ed0a6993d2a829089/view) |
| `malls.txt` | editorial list (Wikipedia "List of shopping malls in Singapore"), names OneMap-searchable |
| `mrt_exits.geojson` | [LTA MRT/LRT Station Exit](https://data.gov.sg/datasets/d_b39d3a0871985372d7e1637193335da5/view) |
| `hawker_centres.geojson` | [NEA Hawker Centres](https://data.gov.sg/datasets/d_4a086da0a5553be1d89383cd90d07ecd/view) |
| `extra_communityclub.geojson` | [PA Community Clubs](https://data.gov.sg/datasets/d_9de02d3fb33d96da1855f4fbef549a0f/view) |
| `ecda_centres.json` + `childcare_centres.geojson` | [ECDA Listing of Centres](https://data.gov.sg/datasets/d_696c994c50745b079b3684f0e90ffc53/view) + [Child Care Services](https://data.gov.sg/datasets/d_5d668e3f544335f8028f546827b773b4/view) (infant-care filter) |
| `rents.json` | [Renting Out of Flats from Jan 2021](https://data.gov.sg/datasets/d_c9f57187485a850908655db0e8cfe651/view) (HDB, last 12 months kept) |
| `hdb_blocks_base.json` | HDB block centroids derived from [HDB Existing Building](https://data.gov.sg/datasets/d_16b157c52ed637edd6ba1232e026258d/view) (see the [atm-500m](https://github.com/fang89/atm-500m) pipeline) |

Any additional `data/extra_<name>.geojson` you drop in is picked up
automatically as a new layer (childcare centres, gyms, polyclinics…).

## Run locally

```bash
cd docs && python3 -m http.server 8000   # then open http://localhost:8000
```

## Deploy (free)

Push to GitHub → repo Settings → Pages → "Deploy from a branch" → branch
`main`, folder `/docs`. Plain static HTML + JSON, no build step.

## Method & caveats

- **Distances are straight-line** from the HDB building centroid; real walking
  routes are longer. MRT/LRT distance is to the *station* (mean of its exits).
- **Score (0–10)** = weighted sum (weights above, editorial ordering). Full
  weight within the benchmark (supermarket/hawker 500 m, MRT/infant care
  800 m, school/mall/CC 1 km), half within 1.5×. Rent: block average over
  the last 12 months vs the island average for the same flat types — ratio
  ≤0.95 → full, ≤1.10 → half; blocks with <3 rentals use their town's
  ratio; no data → neutral half. Abundance is shown in the block panel but
  not scored. Rents are owner-declared HDB approvals — indicative only.
  The top-50 table excludes blocks without a known dwelling-unit count
  (carparks/commercial buildings).
- **Benchmarks are editorial yardsticks**, adjustable in the UI — they are
  not official standards.
- The HDB layer includes **every HDB building** (some are carparks or
  commercial blocks), so a few "blocks" have no residents.
- Supermarkets are **FairPrice and Sheng Siong only**, per the licence
  register; an estate may be well served by Giant/Cold Storage/Prime and still
  show as a "gap".
- MOE's 1 km / 2 km home-to-school priority zones are defined by SLA per
  address, which differs slightly from centroid straight-line distance.
- The mall list is editorial (~110 major malls); neighbourhood strip malls are
  excluded.

## Sources & licences

Data: [data.gov.sg](https://data.gov.sg) datasets (SFA, MOE, LTA, NEA, PA,
HDB) under the
[Singapore Open Data Licence](https://data.gov.sg/open-data-licence).
Geocoding: [OneMap](https://www.onemap.gov.sg/), Singapore Land Authority.
Basemap: © OpenStreetMap contributors, © CARTO. Mall list adapted from
Wikipedia (CC BY-SA).
