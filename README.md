# World Inflation Tracker

A dark, glass-panel dashboard tracking inflation for every country the World
Bank reports on, with a rotatable 3D globe as the centerpiece, a sortable
rankings table, a two-country comparison view, and a per-country detail page
with historical trend and news.

**Live site:** https://saurabhdolas01.github.io/World-Inflation-Tracker/

<div align="center">
  <sub>Matte black · storm grey glass · safety orange — no blue anywhere in the UI.</sub>
</div>

---

## Status

Being built stage by stage, each one reviewed before moving to the next. See
[PLAN.md](PLAN.md) for the full design and build plan.

| Stage | View | Status |
|---|---|---|
| 1 | Data pipeline (World Bank + IMF) | ✅ Done |
| 1 | Map — 3D globe, year selector, search | ✅ Done |
| 2 | Rankings — sortable table, regional breakdown | 🔜 Next |
| 3 | Compare — two-country side by side | ⏳ Planned |
| 4 | Country Detail — history, other indicators, news | ⏳ Planned |

## Features

- **Map** — a rotatable, clickable 3D globe shaded by inflation level
  (`globe.gl`), a year dropdown, country search, and a grey-to-orange legend.
- **Rankings** *(coming next)* — every country sorted by inflation, with a
  world-average/highest/lowest KPI strip, a regional breakdown, and a
  12-month trend sparkline per row.
- **Compare** *(planned)* — exactly two countries side by side: a monthly
  YoY line chart plus GDP growth, unemployment, FX rate, and current account.
- **Country Detail** *(planned)* — headline number, all-time high/low/
  average, a scrollable 2000–2025 history chart, other indicators, and a
  live news feed from Google News.

## Architecture

```
index.html          single-page app shell (hash-routed: #/map, #/rankings, #/compare)
css/styles.css       design tokens + layout for every view
js/
  app.js             router, view transitions, nav/search/info modal
  data.js            fetches + caches data/processed/metrics.json
  format.js          number formatting + the inflation color scale
  globe.js           globe.gl choropleth globe
  views/map.js       Map view (more views land here in later stages)
scripts/
  fetch_data.py      pulls raw World Bank + IMF data into data/raw/
  build_data.py      processes data/raw/ into data/processed/metrics.json
  make_sample_data.py  generates fixture data for offline development
  countries.py       the curated major-economies list (for IMF monthly data)
data/
  raw/               untouched API responses (git-ignored, regenerated each run)
  processed/         metrics.json — what the site actually reads
tests/               unit tests for the data pipeline
.github/workflows/
  update-data.yml    monthly scheduled refresh, commits data/processed/
  pages.yml          deploys main to GitHub Pages on every push
```

The site itself is static: plain HTML/CSS/JS, no build step, no framework.

## Local development

Serve the folder with any static file server (fetching `data/processed/
metrics.json` needs an actual server, not a `file://` URL):

```bash
python3 -m http.server 8000
```

The data pipeline is plain Python (standard library only, no dependencies to
run it):

```bash
cd scripts
python fetch_data.py       # pulls raw World Bank + IMF data into data/raw/
python build_data.py       # processes it into data/processed/metrics.json
```

`make_sample_data.py` generates fixture data shaped exactly like the real
API responses, for working on the front end without hitting live APIs:

```bash
cd scripts
python make_sample_data.py
python build_data.py
```

Run the test suite from the repo root:

```bash
pip install -r scripts/requirements.txt
python -m pytest tests -v
```

## Data sources

| Source | Used for | Refresh |
|---|---|---|
| [World Bank Open Data API](https://api.worldbank.org/v2/) | CPI inflation, GDP growth, unemployment, FX rate, current account — every reporting country | Monthly |
| [IMF International Financial Statistics](https://data.imf.org/) | Monthly CPI index for major economies, converted to YoY % | Monthly |
| [Google News RSS](https://news.google.com/rss) | Per-country headlines (Country Detail view) | Daily *(added in a later stage)* |

Figures can lag the current date by a year or more for countries that report
infrequently — the site surfaces whatever the latest available year is per
country rather than hiding gaps.

## Deployment

Two scheduled/triggered GitHub Actions do all the work:

- **`update-data.yml`** — runs monthly, re-fetches World Bank + IMF data,
  rebuilds `data/processed/metrics.json`, and commits it if anything changed.
- **`pages.yml`** — deploys the `main` branch to GitHub Pages on every push.

To enable Pages on a fork: **Settings → Pages → Source: GitHub Actions**
(the repo must be public, or you'll need GitHub Enterprise for private Pages).

## License

MIT, see [LICENSE](LICENSE).
