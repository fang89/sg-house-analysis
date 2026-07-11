# Every HDB block vs its daily amenities

Interactive map of how far every HDB block in Singapore is from the nearest:

- **FairPrice / Sheng Siong supermarket** (216 stores, SFA licence register)
- **Primary school** (182 schools, MOE School Directory)
- **Shopping mall** (110 major malls, editorial list)
- **MRT / LRT station** (186, position = mean of the LTA exit layer)
- **Hawker centre** (129, NEA) — plus **community clubs** (130)

**Search a postal code / address (OneMap) or click any block** to focus it:
dashed lines point to the nearest of each amenity, everything within 1 km
appears around it, and a panel lists the lot — how many of each amenity are
nearby, the runner-up option, and "between two stations" when that's the case.
Or switch to the **amenity score** view: each block scored **0–10** — the five
everyday amenity types (supermarket, primary school, mall, MRT/LRT, hawker)
each give 2 points within their benchmark distance, 1 point within 1.5× it.
Every layer can be overlaid as markers on the map.

**Live dashboard:** https://fang89.github.io/hdb-amenities/ *(after Pages is enabled)*

## Headline findings (2026-07-11)

- **65%** of HDB blocks are within 500 m of a FairPrice or Sheng Siong;
  4,662 blocks are beyond that (worst ≈ 3.3 km, in estates served mainly by
  other chains)
- **97%** are within 1 km of a primary school
- **72%** are within 800 m of an MRT/LRT station (median 550 m)
- Hawker centres are the scarcest headline amenity: median 640 m, only **39%**
  of blocks within 500 m
- **16%** of blocks score a perfect 10/10 (all five everyday amenities within
  a comfortable walk); Tengah, Pasir Ris and Yishun have the lowest average
  scores (new estates where amenities are still building out)

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
- **Amenity score (0–10)**: supermarket, primary school, mall, MRT/LRT and
  hawker centre each contribute 2 pts if the nearest is within its benchmark
  (supermarket/hawker 500 m, MRT 800 m, school/mall 1 km), 1 pt within 1.5×
  the benchmark, 0 beyond. Types weigh equally; abundance (several of one
  type) is shown in the block panel but not scored. Community clubs are
  mapped, not scored.
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
