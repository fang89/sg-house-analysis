# Every HDB block vs its daily amenities

Interactive map of how far every HDB block in Singapore is from the nearest:

- **FairPrice / Sheng Siong supermarket** (216 stores, SFA licence register)
- **Primary school** (182 schools, MOE School Directory)
- **Shopping mall** (110 major malls, editorial list)
- **MRT / LRT station exit** (186 stations, 597 exits, LTA)
- **Hawker centre** (129, NEA) — plus **CHAS GP clinics** (1,052), **community
  clubs** (130), **public libraries** (27) and **parks** (461)

Pick any amenity to colour the ~13,400 blocks by distance (gap / heat view), or
switch to the **5-amenity score** to see which neighbourhoods have a
supermarket, primary school, mall, MRT exit *and* hawker centre all within
walking distance. Every layer can be overlaid as markers on the map.

**Live dashboard:** https://fang89.github.io/hdb-amenities/ *(after Pages is enabled)*

## Headline findings (2026-07-11)

- **65%** of HDB blocks are within 500 m of a FairPrice or Sheng Siong;
  4,662 blocks are beyond that (worst ≈ 3.3 km, in estates served mainly by
  other chains)
- **97%** are within 1 km of a primary school
- **75%** are within 800 m of an MRT/LRT exit (median 505 m)
- Hawker centres are the scarcest headline amenity: median 640 m, only **39%**
  of blocks within 500 m
- **17%** of blocks have all 5 headline amenities within their benchmark
  distances; Tengah, Pasir Ris and Yishun have the lowest average scores
  (new estates where amenities are still building out)

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
| `extra_clinic.geojson` | [MOH CHAS Clinics](https://data.gov.sg/datasets/d_548c33ea2d99e29ec63a7cc9edcccedc/view) (medical only, dental dropped) |
| `extra_communityclub.geojson` | [PA Community Clubs](https://data.gov.sg/datasets/d_9de02d3fb33d96da1855f4fbef549a0f/view) |
| `extra_library.geojson` | [NLB Libraries](https://data.gov.sg/datasets/d_27b8dae65d9ca1539e14d09578b17cbf/view) |
| `extra_park.geojson` | [NParks Parks](https://data.gov.sg/datasets/d_0542d48f0991541706b58059381a6eca/view) |
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
  routes are longer. MRT/LRT distance is to the nearest *station exit*.
- **Benchmarks are editorial yardsticks** (supermarket/hawker/clinic 500 m,
  MRT/park 800 m, school/mall/CC 1 km, library 2 km), adjustable in the UI —
  they are not official standards.
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

Data: [data.gov.sg](https://data.gov.sg) datasets (SFA, MOE, LTA, NEA, MOH,
PA, NLB, NParks, HDB) under the
[Singapore Open Data Licence](https://data.gov.sg/open-data-licence).
Geocoding: [OneMap](https://www.onemap.gov.sg/), Singapore Land Authority.
Basemap: © OpenStreetMap contributors, © CARTO. Mall list adapted from
Wikipedia (CC BY-SA).
