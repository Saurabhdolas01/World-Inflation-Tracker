/* The Map (home) view: year dropdown + the 3D choropleth globe + legend. */

(function (global) {
  "use strict";

  let globeHandle = null;
  let selectedYear = null;

  function render(root) {
    root.innerHTML = `
      <div class="map-main">
        <div class="map-layout">
          <div class="map-globe-col">
            <div class="globe-panel glass">
              <div id="globe-container"></div>
              <div class="globe-loading" id="globe-loading">
                <div class="spinner"></div>
                <span>Loading globe…</span>
              </div>
            </div>
            <div class="legend-row">
              <span>0%</span>
              <div class="legend-gradient"></div>
              <span>20%+</span>
              <span style="margin-left:12px;">No data</span>
              <div class="legend-nodata-swatch"></div>
            </div>
          </div>

          <div class="map-side-col">
            <div class="map-kpi-strip glass" id="map-kpi-strip"></div>
            <div class="map-movers-panel glass">
              <div class="panel-title">Highest inflation, selected year</div>
              <div id="map-movers-list"></div>
            </div>
          </div>
        </div>
      </div>
    `;

    const yearSelect = document.getElementById("year-select");

    TrackerData.load()
      .then((metrics) => {
        setupYearDropdown(metrics, yearSelect);
        mountGlobe(metrics);
        renderSidePanel(metrics);
      })
      .catch((err) => {
        console.error("[map] failed to load data:", err);
        root.querySelector(".map-main").innerHTML =
          `<div class="placeholder-view"><span>Could not load inflation data.</span><span style="font-size:11px;">${err.message}</span></div>`;
      });
  }

  function setupYearDropdown(metrics, yearSelect) {
    const years = TrackerData.availableYears(metrics);
    yearSelect.innerHTML = years.map((y) => `<option value="${y}">${y}</option>`).join("");
    selectedYear = years[0] || new Date().getFullYear();
    yearSelect.value = String(selectedYear);

    yearSelect.onchange = () => {
      selectedYear = parseInt(yearSelect.value, 10);
      if (globeHandle) {
        globeHandle.refreshColors(() => valueGetter(metrics));
      }
      renderSidePanel(metrics);
    };
  }

  // Values for the selected year, per country, computed once per render so
  // the KPI strip and movers list agree with what's actually colored on the
  // globe (both read from the same Fmt.valueForYear fallback logic).
  function valuesForSelectedYear(metrics) {
    return metrics.countries
      .map((c) => ({ country: c, value: Fmt.valueForYear(c.inflation_history, selectedYear) }))
      .filter((r) => r.value !== null);
  }

  function renderSidePanel(metrics) {
    const rows = valuesForSelectedYear(metrics);
    const kpiStrip = document.getElementById("map-kpi-strip");
    const moversList = document.getElementById("map-movers-list");
    if (!kpiStrip || !moversList) return; // view may have been torn down mid-fetch

    if (!rows.length) {
      kpiStrip.innerHTML = `<div class="map-kpi-item"><span class="map-kpi-label">No data for ${selectedYear}</span></div>`;
      moversList.innerHTML = "";
      return;
    }

    const values = rows.map((r) => r.value);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const sorted = rows.slice().sort((a, b) => b.value - a.value);
    const lowest = sorted[sorted.length - 1];

    kpiStrip.innerHTML = `
      <div class="map-kpi-item">
        <span class="map-kpi-label">World average, ${selectedYear}</span>
        <span class="map-kpi-value mono">${avg.toFixed(1)}%</span>
      </div>
      <div class="map-kpi-item">
        <span class="map-kpi-label">Lowest</span>
        <span class="map-kpi-value mono" style="color:var(--good);">${lowest.country.name}, ${lowest.value.toFixed(1)}%</span>
      </div>
      <div class="map-kpi-item">
        <span class="map-kpi-label">Reporting countries</span>
        <span class="map-kpi-value mono">${rows.length}</span>
      </div>
    `;

    moversList.innerHTML = sorted
      .slice(0, 8)
      .map(
        (r, i) => `
        <button class="mover-row" data-iso3="${r.country.iso3}">
          <span class="mover-rank mono">${i + 1}</span>
          <span class="mover-name">${r.country.name}</span>
          <span class="mover-value mono" style="color:${Fmt.inflationColor(r.value)};">${r.value.toFixed(1)}%</span>
        </button>`
      )
      .join("");

    moversList.querySelectorAll(".mover-row").forEach((btn) => {
      btn.addEventListener("click", () => {
        const country = TrackerData.findByIso3(metrics, btn.dataset.iso3);
        focusCountry(country);
      });
    });
  }

  function valueGetter(metrics) {
    return (iso3) => {
      const country = TrackerData.findByIso3(metrics, iso3);
      if (!country) return null;
      return Fmt.valueForYear(country.inflation_history, selectedYear);
    };
  }

  function mountGlobe(metrics) {
    const container = document.getElementById("globe-container");
    const loading = document.getElementById("globe-loading");

    if (typeof Globe !== "function") {
      loading.innerHTML = `<span>globe.gl failed to load (check network/CDN access).</span>`;
      return;
    }

    globeHandle = TrackerGlobe.mount(container, {
      getValueForIso3: (iso3) => {
        const getter = valueGetter(metrics);
        return getter(iso3);
      },
      onCountryClick: (iso3) => {
        // Country Detail view ships in a later stage; for now this is a
        // harmless no-op hook left in place so the click wiring doesn't
        // need to be revisited later.
        console.log("[map] clicked country", iso3);
      },
    });

    container.addEventListener("globe:error", () => {
      loading.innerHTML = `<span>Could not load country outlines (network issue). The globe will stay empty until this is retried.</span>`;
    });

    // hide the spinner once the globe has had a moment to initialize; a
    // true "first paint" event isn't exposed by globe.gl, so this is a
    // reasonable approximation rather than something more precise.
    setTimeout(() => {
      if (loading) loading.style.display = "none";
    }, 600);
  }

  function destroy() {
    if (globeHandle) {
      globeHandle.destroy();
      globeHandle = null;
    }
  }

  // Used by the header search box (and the top-movers panel): flies the
  // camera to a country's lat/lon and stops auto-rotation, when a globe is
  // mounted and the country has coordinates.
  function focusCountry(country) {
    if (!globeHandle || !country || country.lat === null || country.lon === null) return;
    globeHandle.flyTo(country.lat, country.lon);
  }

  global.MapView = { render, destroy, focusCountry };
})(window);
