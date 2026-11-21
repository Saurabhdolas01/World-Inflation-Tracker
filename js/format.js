/* Shared formatting helpers + the inflation color scale, used by every view
   so the globe, the rankings table, and the compare/detail charts all agree
   on what color a given inflation level gets. */

(function (global) {
  "use strict";

  function formatPct(value, digits) {
    if (value === null || value === undefined || Number.isNaN(value)) return "No data";
    const d = digits === undefined ? 1 : digits;
    return `${value.toFixed(d)}%`;
  }

  function formatSignedPct(value, digits) {
    if (value === null || value === undefined || Number.isNaN(value)) return "No data";
    const d = digits === undefined ? 1 : digits;
    const sign = value > 0 ? "+" : "";
    return `${sign}${value.toFixed(d)}%`;
  }

  function changeArrow(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return "";
    return value >= 0 ? "▲" : "▼"; // ▲ / ▼
  }

  // Inflation legend: 0% -> storm grey, 20%+ -> safety orange, matching the
  // approved mockup's legend gradient exactly (same 4 hex stops).
  const SCALE_STOPS = [
    { at: 0.0, color: [58, 58, 62] },     // #3a3a3e
    { at: 0.33, color: [107, 107, 112] }, // #6b6b70
    { at: 0.66, color: [168, 168, 173] }, // #a8a8ad
    { at: 1.0, color: [255, 106, 19] },   // #ff6a13 (accent)
  ];
  const SCALE_DOMAIN_MAX = 20; // "20%+" per the legend

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function inflationColor(value) {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return "#2c2c2a"; // no-data swatch base color
    }
    const t = Math.max(0, Math.min(1, value / SCALE_DOMAIN_MAX));
    let lo = SCALE_STOPS[0];
    let hi = SCALE_STOPS[SCALE_STOPS.length - 1];
    for (let i = 0; i < SCALE_STOPS.length - 1; i++) {
      if (t >= SCALE_STOPS[i].at && t <= SCALE_STOPS[i + 1].at) {
        lo = SCALE_STOPS[i];
        hi = SCALE_STOPS[i + 1];
        break;
      }
    }
    const span = hi.at - lo.at || 1;
    const localT = (t - lo.at) / span;
    const r = Math.round(lerp(lo.color[0], hi.color[0], localT));
    const g = Math.round(lerp(lo.color[1], hi.color[1], localT));
    const b = Math.round(lerp(lo.color[2], hi.color[2], localT));
    return `rgb(${r}, ${g}, ${b})`;
  }

  function valueForYear(history, year) {
    if (!history || !history.length) return null;
    const exact = history.find((p) => p.year === year);
    if (exact) return exact.value;
    // fall back to the latest year at or before the requested one, since
    // many countries report with a lag
    const prior = history.filter((p) => p.year <= year).sort((a, b) => b.year - a.year)[0];
    return prior ? prior.value : null;
  }

  global.Fmt = {
    formatPct,
    formatSignedPct,
    changeArrow,
    inflationColor,
    valueForYear,
  };
})(window);
