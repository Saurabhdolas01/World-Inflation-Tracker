/* The Map (home) view: year dropdown + the 3D choropleth globe + legend. */

(function (global) {
  "use strict";

  let globeHandle = null;
  let selectedYear = null;

  function render(root) {
    root.innerHTML = `
      <div class="map-main">
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
    `;

    const yearSelect = document.getElementById("year-select");

    TrackerData.load()
      .then((metrics) => {
        setupYearDropdown(metrics, yearSelect);
        mountGlobe(metrics);
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
    };
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

  // Used by the header search box: flies the camera to a country's
  // lat/lon, when a globe is mounted and the country has coordinates.
  function focusCountry(country) {
    if (!globeHandle || !country || country.lat === null || country.lon === null) return;
    globeHandle.instance.pointOfView({ lat: country.lat, lng: country.lon, altitude: 1.6 }, 1000);
  }

  global.MapView = { render, destroy, focusCountry };
})(window);
