# World Inflation Tracker: build plan

A dark, glass-panel dashboard tracking inflation (and a few supporting
indicators) for every country the World Bank reports on, with a rotatable 3D
globe as the centerpiece, a sortable rankings table, a 2-country comparison
view, and a per-country detail page with historical trend and news.

This plan reflects the design approved in the mockup phase (see the project's
design artifact) and is being built stage by stage so each piece can be
reviewed before moving to the next.

## Visual language

- Background: matte black (`#141414`)
- Panels: storm-grey glass (`rgba(170,172,180,0.065)` + `backdrop-filter: blur(18px)`)
- Accent: safety orange (`#ff6a13`), used for the active nav tab, the logo
  mark, chart highlights, and the top end of the inflation legend
- No blue anywhere in the UI chrome. Status colors (good/warning/critical,
  green/amber/red) are a semantic exception, used only for up/down and
  severity, the same way a stock ticker uses red/green.
- Fonts: Plus Jakarta Sans (numbers, headings) + Inter (body/UI)
- Rounded corners, hover/active micro-transitions, and smooth tab-to-tab
  transitions across all four views (Map, Rankings, Compare, Country Detail)

## Pages

1. **Map (home)**: header (logo, nav, search, info), a year dropdown, and a
   3D rotatable/clickable globe (`globe.gl`) shaded by inflation level, with a
   grey-to-orange legend strip. Clicking a country opens its detail page.
2. **Rankings**: searchable/filterable table of every country sorted by
   inflation, with a KPI strip (world average, highest, lowest, count above
   10%), a regional-average bar breakdown, per-region "highest inflation"
   leader cards, and a trend sparkline + severity bar per row.
3. **Compare**: exactly two countries side by side: a YoY line chart, latest
   snapshot cards, and a row-by-row comparison of other economic indicators
   (GDP growth, unemployment, FX rate, current account).
4. **Country Detail** (full page, not a popup): headline number + change
   badge, all-time high/low/average, a scrollable historical line chart
   (2000-2025), other indicators (GDP growth, unemployment, FX rate, current
   account, central bank rate, fiscal deficit, the last two marked "no data"
   where unavailable), and a scrollable "latest news" list pulled from
   Google News RSS.

## Data

- **World Bank API**: annual data for every country (not just a curated
  list): CPI inflation (`FP.CPI.TOTL.ZG`), GDP growth (`NY.GDP.MKTP.KD.ZG`),
  unemployment (`SL.UEM.TOTL.ZS`), FX rate vs USD (`PA.NUS.FCRF`), current
  account (`BN.CAB.XOKA.GD.ZS`). Country metadata (name, region, lat/lon) is
  pulled from `/v2/country` and used to drop aggregate "regions" from the
  per-country list.
- **IMF International Financial Statistics (IFS)**: monthly CPI index for a
  set of major economies (G20 + a few regional anchors), converted to YoY %
  for the Compare view's monthly trend line.
- **Google News RSS**: top headlines per country for the detail page's news
  section, fetched server-side during a scheduled refresh (not client-side).

## Refresh cadence

- Economic data (World Bank + IMF): monthly, via a scheduled GitHub Action
  that runs `scripts/fetch_data.py` then `scripts/build_data.py` and commits
  the refreshed `data/processed/*.json`.
- News: daily, via a separate scheduled Action (added once the Country
  Detail / news stage is built).
- Site: static, deployed to GitHub Pages on every push to `main`.

## Build stages

1. Data pipeline (World Bank fetch for all countries + IMF monthly for
   majors) + Map page, including the real `globe.gl` globe. ✅ Done
2. Rankings page. ✅ Done
3. Compare page. 🔜 Next
4. Country Detail page + Google News integration + its own scheduled Action.

Each stage is reviewed before moving to the next.
