/* Builds the 3D choropleth globe with globe.gl (bundles three.js, loaded via
   CDN in index.html as the global `Globe`).

   Design choice, stated plainly rather than guessed at silently: the brief
   asked for a literal "Google Earth style" rotating globe, but the approved
   palette is storm grey / matte black / safety orange only, no blue -- a
   photographic Earth texture would put blue oceans back in. So instead of
   an image-textured globe, this renders country polygons as a choropleth
   (oceans are just the dark background, land is colored by inflation
   level), which keeps the interaction model (rotate, zoom, click, hover)
   the brief asked for without reintroducing blue. Flagging this so it can
   be revisited if a photographic look turns out to matter more than the
   palette rule.

   NOT verified in a live browser from this environment (no graphical
   browser / live network here) -- written against globe.gl's documented
   API and the standard Natural Earth country-polygon dataset its own demos
   use. Check the globe actually renders once this is deployed. */

(function (global) {
  "use strict";

  const COUNTRY_GEOJSON_URL =
    "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson";

  let geoFeatures = null;
  let geoFetchPromise = null;

  function loadGeoJson() {
    if (geoFeatures) return Promise.resolve(geoFeatures);
    if (geoFetchPromise) return geoFetchPromise;
    geoFetchPromise = fetch(COUNTRY_GEOJSON_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`country geojson: HTTP ${res.status}`);
        return res.json();
      })
      .then((geo) => {
        geoFeatures = geo.features || [];
        return geoFeatures;
      });
    return geoFetchPromise;
  }

  function isoOf(feature) {
    const p = feature.properties || {};
    return p.ISO_A3 || p.ADM0_A3 || p.iso_a3 || null;
  }

  /**
   * Mounts a choropleth globe into `container`.
   * `getValueForIso3(iso3)` should return the inflation value (or null) for
   * the currently-selected year -- the caller owns the year state so the
   * globe can be recolored without rebuilding it.
   * `onCountryClick(iso3)` fires on click, for future "open country detail"
   * wiring (stage 4).
   */
  function mount(container, { getValueForIso3, onCountryClick }) {
    // Kept in a mutable box so refreshColors() can swap in a new accessor
    // (e.g. after the year dropdown changes) without rebuilding the globe.
    const state = { getValueForIso3 };

    const instance = Globe()(container)
      .backgroundColor("rgba(0,0,0,0)")
      .showGlobe(true)
      .globeImageUrl(null)
      .showAtmosphere(true)
      .atmosphereColor("#ff6a13")
      .atmosphereAltitude(0.18)
      .polygonCapColor((feat) => {
        const value = state.getValueForIso3(isoOf(feat));
        return global.Fmt.inflationColor(value);
      })
      .polygonSideColor(() => "rgba(20,20,20,0.6)")
      .polygonStrokeColor(() => "rgba(170,172,180,0.35)")
      .polygonAltitude(0.006)
      .polygonLabel((feat) => {
        const iso3 = isoOf(feat);
        const value = getValueForIso3(iso3);
        const name = (feat.properties || {}).ADMIN || (feat.properties || {}).NAME || iso3;
        const valueStr = global.Fmt.formatPct(value);
        return `<div class="globe-tooltip"><span class="name">${name}</span><br><span class="val">${valueStr}</span> inflation</div>`;
      })
      .onPolygonClick((feat) => {
        instance.controls().autoRotate = false;
        const iso3 = isoOf(feat);
        if (iso3 && onCountryClick) onCountryClick(iso3);
      });

    // globe.gl's underlying three.js scene has a transparent/dark base
    // by default when no globeImageUrl is set; give the sphere itself a
    // matte-black material so "oceans" read as the dashboard background,
    // not as a flat grey ball.
    try {
      const globeMaterial = instance.globeMaterial();
      globeMaterial.color.set("#141414");
      globeMaterial.opacity = 1;
    } catch (e) {
      // globe.gl internals can change across versions -- non-fatal if this
      // doesn't apply; the globe still renders, just without the tuned
      // sphere material.
      console.warn("[globe] could not set custom globe material:", e);
    }

    instance.controls().autoRotate = true;
    instance.controls().autoRotateSpeed = 0.5;
    // Any manual drag/zoom permanently stops auto-rotation (it should not
    // resume once the person has taken control of the view).
    instance.controls().addEventListener("start", () => {
      instance.controls().autoRotate = false;
    });

    function resize() {
      instance.width(container.clientWidth);
      instance.height(container.clientHeight);
    }
    window.addEventListener("resize", resize);
    resize();

    loadGeoJson()
      .then((features) => {
        instance.polygonsData(features);
      })
      .catch((err) => {
        console.error("[globe] failed to load country polygons:", err);
        container.dispatchEvent(new CustomEvent("globe:error", { detail: err }));
      });

    return {
      instance,
      // Call after the year selection changes (or anything else that
      // affects getValueForIso3's result) to recolor without rebuilding.
      refreshColors(newGetValueForIso3) {
        if (newGetValueForIso3) state.getValueForIso3 = newGetValueForIso3;
        const data = instance.polygonsData();
        instance.polygonsData([]);
        instance.polygonsData(data);
      },
      flyTo(lat, lng, altitude) {
        instance.controls().autoRotate = false;
        instance.pointOfView({ lat, lng, altitude: altitude || 1.6 }, 1000);
      },
      destroy() {
        window.removeEventListener("resize", resize);
      },
    };
  }

  global.TrackerGlobe = { mount };
})(window);
