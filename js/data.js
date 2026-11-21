/* Loads data/processed/metrics.json once and makes it available to every
   view. All views share this single fetch + cache rather than reloading. */

(function (global) {
  "use strict";

  let cached = null;
  let inflight = null;

  function load() {
    if (cached) return Promise.resolve(cached);
    if (inflight) return inflight;
    inflight = fetch("data/processed/metrics.json")
      .then((res) => {
        if (!res.ok) throw new Error(`metrics.json: HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        cached = json;
        inflight = null;
        return json;
      })
      .catch((err) => {
        inflight = null;
        throw err;
      });
    return inflight;
  }

  function availableYears(metrics) {
    const years = new Set();
    metrics.countries.forEach((c) => {
      (c.inflation_history || []).forEach((p) => years.add(p.year));
    });
    return Array.from(years).sort((a, b) => b - a);
  }

  function findByIso3(metrics, iso3) {
    return metrics.countries.find((c) => c.iso3 === iso3) || null;
  }

  function searchByName(metrics, query) {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return metrics.countries.filter((c) => c.name.toLowerCase().includes(q));
  }

  global.TrackerData = { load, availableYears, findByIso3, searchByName };
})(window);
