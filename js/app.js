/* App shell: hash router, cross-view fade/slide transitions, nav active
   state, search box, info modal. Rankings/Compare/Country Detail routes
   render a placeholder until their stages are built. */

(function () {
  "use strict";

  const global = window;
  const viewRoot = document.getElementById("view-root");
  const mapSubheader = document.getElementById("map-subheader");
  const navLinks = Array.from(document.querySelectorAll("#main-nav a"));

  const VIEWS = {
    map: {
      render: (el) => global.MapView.render(el),
      destroy: () => global.MapView.destroy && global.MapView.destroy(),
      showSubheader: true,
    },
    rankings: { render: renderPlaceholder("Rankings"), destroy: noop, showSubheader: false },
    compare: { render: renderPlaceholder("Compare"), destroy: noop, showSubheader: false },
  };

  let currentRouteKey = null;

  function noop() {}

  function renderPlaceholder(label) {
    return (el) => {
      el.innerHTML = `
        <div class="placeholder-view">
          <span>${label} is coming in a later build stage.</span>
          <span style="font-size:11px;">The Map view (and the data pipeline behind it) ships first.</span>
        </div>`;
    };
  }

  function routeFromHash() {
    const hash = window.location.hash.replace(/^#\/?/, "");
    const key = hash.split("/")[0];
    return VIEWS[key] ? key : "map";
  }

  function setActiveNav(routeKey) {
    navLinks.forEach((a) => {
      a.classList.toggle("active", a.dataset.route === routeKey);
    });
  }

  function navigate() {
    const routeKey = routeFromHash();
    if (routeKey === currentRouteKey) return;

    const view = VIEWS[routeKey];
    const outgoingEl = viewRoot.querySelector(".view");

    function mountIncoming() {
      if (currentRouteKey && VIEWS[currentRouteKey]) {
        VIEWS[currentRouteKey].destroy();
      }

      const el = document.createElement("div");
      el.className = "view view-enter";
      viewRoot.appendChild(el);
      view.render(el);

      mapSubheader.style.display = view.showSubheader ? "flex" : "none";
      setActiveNav(routeKey);
      currentRouteKey = routeKey;

      // force layout so the enter transition actually animates from the
      // view-enter state rather than snapping straight to view-enter-active
      requestAnimationFrame(() => {
        el.classList.add("view-enter-active");
        el.classList.remove("view-enter");
      });
    }

    if (outgoingEl) {
      outgoingEl.classList.add("view-exit-active");
      setTimeout(() => {
        outgoingEl.remove();
        mountIncoming();
      }, 160);
    } else {
      mountIncoming();
    }
  }

  function setupSearch() {
    const form = document.getElementById("country-search-form");
    const input = document.getElementById("country-search");
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = input.value.trim();
      if (!query) return;
      TrackerData.load().then((metrics) => {
        const matches = TrackerData.searchByName(metrics, query);
        if (!matches.length) return;
        if (currentRouteKey === "map" && global.MapView.focusCountry) {
          global.MapView.focusCountry(matches[0]);
        }
      });
    });
  }

  function setupInfoModal() {
    const modal = document.getElementById("info-modal");
    const openBtn = document.getElementById("info-btn");
    const closeBtn = document.getElementById("info-close-btn");
    openBtn.addEventListener("click", () => modal.classList.add("open"));
    closeBtn.addEventListener("click", () => modal.classList.remove("open"));
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("open");
    });
  }

  function init() {
    setupSearch();
    setupInfoModal();
    window.addEventListener("hashchange", navigate);
    if (!window.location.hash) window.location.hash = "#/map";
    navigate();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
