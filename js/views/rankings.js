/* The Rankings view: KPI strip, regional breakdown, per-region leader
   cards, and the full sortable/searchable/filterable country table. */

(function (global) {
  "use strict";

  const REGION_ORDER = ["Americas", "Europe", "Asia-Pacific", "Middle East & Africa"];

  let state = {
    metrics: null,
    search: "",
    region: "All regions",
    sortKey: "latest_inflation",
    sortDir: "desc",
  };

  function render(root) {
    root.innerHTML = `
      <div class="rankings-main">
        <div class="rankings-filterbar glass">
          <form role="search" class="search-box" id="rankings-search-form" style="width:240px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#7c7c82" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <label for="rankings-search" class="sr-only">Search country</label>
            <input id="rankings-search" type="text" placeholder="Search country" autocomplete="off">
          </form>
          <label for="region-filter" class="sr-only">Filter by region</label>
          <select id="region-filter" class="select-pill" style="padding:5px 10px; font-weight:400;"></select>
          <div style="flex:1;"></div>
          <span class="count" id="rankings-count"></span>
        </div>

        <div class="rankings-kpi-row">
          <div class="kpi-tile-grid" id="kpi-tile-grid"></div>
          <div class="region-bar-panel glass">
            <div class="panel-title">Average inflation by region</div>
            <div id="region-bar-list"></div>
          </div>
        </div>

        <div class="leader-card-row">
          <div class="panel-title">Highest inflation by region</div>
          <div class="leader-card-grid" id="leader-card-grid"></div>
        </div>

        <div class="rankings-table-wrap">
          <table class="rankings-table" id="rankings-table">
            <thead>
              <tr>
                <th data-sort="rank">#</th>
                <th data-sort="name">Country</th>
                <th data-sort="latest_inflation" class="num">Inflation</th>
                <th data-sort="change_vs_prev_year" class="num">Change</th>
                <th>Trend</th>
                <th>Scale</th>
              </tr>
            </thead>
            <tbody id="rankings-tbody"></tbody>
          </table>
        </div>
      </div>
    `;

    TrackerData.load()
      .then((metrics) => {
        state.metrics = metrics;
        setupFilterBar(metrics);
        setupSortableHeaders();
        renderKpiTiles(metrics);
        renderRegionBars(metrics);
        renderLeaderCards(metrics);
        renderTable();
      })
      .catch((err) => {
        console.error("[rankings] failed to load data:", err);
        root.querySelector(".rankings-main").innerHTML =
          `<div class="placeholder-view"><span>Could not load inflation data.</span><span style="font-size:11px;">${err.message}</span></div>`;
      });
  }

  function setupFilterBar(metrics) {
    const searchInput = document.getElementById("rankings-search");
    const searchForm = document.getElementById("rankings-search-form");
    const regionSelect = document.getElementById("region-filter");

    const regions = Array.from(new Set(metrics.countries.map((c) => c.region))).sort();
    regionSelect.innerHTML = ["All regions", ...regions]
      .map((r) => `<option value="${r}">${r}</option>`)
      .join("");

    searchForm.addEventListener("submit", (e) => e.preventDefault());
    searchInput.addEventListener("input", () => {
      state.search = searchInput.value;
      renderTable();
    });
    regionSelect.addEventListener("change", () => {
      state.region = regionSelect.value;
      renderTable();
    });
  }

  function setupSortableHeaders() {
    document.querySelectorAll("#rankings-table th[data-sort]").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (state.sortKey === key) {
          state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        } else {
          state.sortKey = key;
          state.sortDir = key === "name" ? "asc" : "desc";
        }
        renderTable();
      });
    });
  }

  function renderKpiTiles(metrics) {
    const s = metrics.world_summary;
    const tiles = [
      { label: "World average", value: Fmt.formatPct(s.average_pct), color: "var(--ink)" },
      { label: "Highest", value: s.highest ? `${s.highest.value.toFixed(1)}%` : "No data", color: "var(--critical)" },
      { label: "Lowest", value: s.lowest ? `${s.lowest.value.toFixed(1)}%` : "No data", color: "var(--good)" },
      { label: "Above 10%", value: `${s.above_10_pct_count} <span style="font-size:10px;color:var(--muted);font-weight:500;">countries</span>`, color: "var(--ink)" },
    ];
    document.getElementById("kpi-tile-grid").innerHTML = tiles
      .map(
        (t) => `
        <div class="kpi-tile glass">
          <div class="kpi-label">${t.label}</div>
          <div class="kpi-value mono" style="color:${t.color};">${t.value}</div>
        </div>`
      )
      .join("");
  }

  function renderRegionBars(metrics) {
    const regional = metrics.world_summary.regional_average_pct || {};
    const maxVal = Math.max(...Object.values(regional), 1);
    const order = REGION_ORDER.filter((r) => r in regional).concat(
      Object.keys(regional).filter((r) => !REGION_ORDER.includes(r))
    );
    document.getElementById("region-bar-list").innerHTML = order
      .map((region) => {
        const val = regional[region];
        const pct = Math.max(4, Math.round((val / maxVal) * 100));
        return `
          <div class="region-bar-row">
            <span class="region-name">${region}</span>
            <div class="region-bar-track"><div class="region-bar-fill" style="width:${pct}%;"></div></div>
            <span class="region-value mono">${val.toFixed(1)}%</span>
          </div>`;
      })
      .join("");
  }

  function renderLeaderCards(metrics) {
    const byRegion = {};
    metrics.countries.forEach((c) => {
      if (c.latest_inflation === null) return;
      if (!byRegion[c.region] || c.latest_inflation > byRegion[c.region].latest_inflation) {
        byRegion[c.region] = c;
      }
    });
    const order = REGION_ORDER.filter((r) => r in byRegion).concat(
      Object.keys(byRegion).filter((r) => !REGION_ORDER.includes(r))
    );
    document.getElementById("leader-card-grid").innerHTML = order
      .map((region) => {
        const c = byRegion[region];
        return `
          <div class="leader-card glass">
            <div class="region-name">${region}</div>
            <div>
              <div class="country-name">${c.name}</div>
              <div class="country-value mono" style="color:${severityColor(c.latest_inflation)};">${c.latest_inflation.toFixed(1)}%</div>
            </div>
            <div class="rank-note">rank ${c.rank} of ${metrics.countries.length}</div>
          </div>`;
      })
      .join("");
  }

  function severityColor(value) {
    if (value === null || value === undefined) return "var(--muted)";
    if (value > 10) return "var(--critical)";
    if (value >= 4) return "var(--warning)";
    return "var(--good)";
  }

  function filteredSortedCountries() {
    const { metrics, search, region, sortKey, sortDir } = state;
    let rows = metrics.countries;

    if (region !== "All regions") {
      rows = rows.filter((c) => c.region === region);
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      rows = rows.filter((c) => c.name.toLowerCase().includes(q));
    }

    const dir = sortDir === "asc" ? 1 : -1;
    rows = rows.slice().sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];
      if (av === null || av === undefined) av = sortKey === "name" ? "" : -Infinity;
      if (bv === null || bv === undefined) bv = sortKey === "name" ? "" : -Infinity;
      if (typeof av === "string") return av.localeCompare(bv) * dir;
      return (av - bv) * dir;
    });
    return rows;
  }

  function sparklinePoints(country) {
    // Prefer the IMF monthly YoY series (major economies only); fall back
    // to the last several years of annual data so every country gets a
    // trend line, not just the ones with monthly coverage.
    let values;
    if (country.monthly_yoy && country.monthly_yoy.length >= 2) {
      values = country.monthly_yoy.slice(-12).map((p) => p.yoy_pct);
    } else {
      values = (country.inflation_history || []).slice(-8).map((p) => p.value);
    }
    if (values.length < 2) return null;

    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const stepX = 60 / (values.length - 1);
    const points = values
      .map((v, i) => {
        const x = Math.round(i * stepX);
        const y = Math.round(18 - ((v - min) / span) * 16);
        return `${x},${y}`;
      })
      .join(" ");
    const trendUp = values[values.length - 1] > values[0];
    return { points, color: trendUp ? "var(--critical)" : "var(--good)" };
  }

  function renderTable() {
    const rows = filteredSortedCountries();
    const { metrics } = state;

    document.getElementById("rankings-count").textContent =
      `${rows.length} ${rows.length === 1 ? "country" : "countries"}, sorted by ${headerLabel(state.sortKey)}, ${state.sortDir === "desc" ? "high to low" : "low to high"}`;

    document.querySelectorAll("#rankings-table th[data-sort]").forEach((th) => {
      th.classList.toggle("sorted", th.dataset.sort === state.sortKey);
    });

    const tbody = document.getElementById("rankings-tbody");
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:var(--muted); padding:20px 10px;">No countries match that search/filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = rows
      .map((c) => {
        const spark = sparklinePoints(c);
        const sparkSvg = spark
          ? `<svg viewBox="0 0 60 20" width="60" height="20"><polyline fill="none" stroke="${spark.color}" stroke-width="1.8" points="${spark.points}"/></svg>`
          : `<span style="color:var(--muted); font-size:10px;">No data</span>`;

        const change = c.change_vs_prev_year;
        const changeColor = change === null ? "var(--muted)" : change >= 0 ? "var(--critical)" : "var(--good)";
        const changeStr = change === null ? "No data" : `${Fmt.changeArrow(change)} ${Math.abs(change).toFixed(1)}%`;

        const sevColor = severityColor(c.latest_inflation);
        const sevWidth = c.latest_inflation === null ? 0 : Math.min(100, Math.round((c.latest_inflation / 45) * 100));

        const highlight = c.iso3 === "IND" ? "highlighted-row" : "";

        return `
          <tr class="${highlight}">
            <td class="mono" style="color:var(--muted);">${c.rank}</td>
            <td style="font-weight:600;">${c.name}<span class="region-chip">${c.region}</span></td>
            <td class="mono num" style="font-weight:700; color:${sevColor};">${c.latest_inflation === null ? "No data" : c.latest_inflation.toFixed(1) + "%"}</td>
            <td class="mono num" style="color:${changeColor};">${changeStr}</td>
            <td class="sparkline-cell">${sparkSvg}</td>
            <td><div class="severity-track"><div class="severity-fill" style="width:${sevWidth}%; background:${sevColor};"></div></div></td>
          </tr>`;
      })
      .join("");
  }

  function headerLabel(key) {
    return { rank: "rank", name: "name", latest_inflation: "inflation", change_vs_prev_year: "change" }[key] || key;
  }

  function destroy() {}

  global.RankingsView = { render, destroy };
})(window);
