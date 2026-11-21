# World Inflation Tracker

A dark, glass-panel dashboard tracking inflation for every country the World
Bank reports on. 3D globe centerpiece, sortable rankings, a two-country
comparison view, and a per-country detail page with history and news.

Live site: https://saurabhdolas01.github.io/world-inflation-tracker/
(enabled once GitHub Pages is turned on for this repo, see below)

## Status

Being built stage by stage. See [PLAN.md](PLAN.md) for the full design and
build plan. Current stage: **data pipeline + Map page**.

## Local development

The site itself is static (plain HTML/CSS/JS, no build step) — just open
`index.html`, or serve the folder with any static file server:

```
python3 -m http.server 8000
```

The data pipeline is Python:

```
cd scripts
pip install -r requirements.txt
python fetch_data.py    # pulls raw World Bank + IMF data into data/raw/
python build_data.py    # processes it into data/processed/metrics.json
```

`make_sample_data.py` generates fixture data shaped like the real API
responses, for working on the front end without hitting the live APIs.

Run tests with:

```
cd scripts && python -m pytest ../tests
```

## Data sources

- [World Bank Open Data API](https://api.worldbank.org/v2/) — annual CPI
  inflation, GDP growth, unemployment, FX rate, current account, for every
  reporting country.
- [IMF International Financial Statistics](https://data.imf.org/) — monthly
  CPI index for major economies, converted to year-over-year % for trend
  charts.
- [Google News RSS](https://news.google.com/rss) — per-country headlines
  (added in a later stage).

## Deployment

A scheduled GitHub Action refreshes the data monthly and commits it; a
second workflow deploys the `main` branch to GitHub Pages on every push.
Enable Pages under **Settings → Pages → Source: GitHub Actions** once the
workflows are pushed.

## License

MIT, see [LICENSE](LICENSE).
