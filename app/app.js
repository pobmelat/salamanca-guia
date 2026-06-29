(() => {
  const DATA = window.GUIDE_DATA;
  const qs = new URLSearchParams(window.location.search);
  const defaultSlug = qs.get("route") || DATA.app.defaultRoute || DATA.routes[0]?.slug;

  const routePicker = document.querySelector("#route-picker");
  const routeTitle = document.querySelector("#route-title");
  const routeSubtitle = document.querySelector("#route-subtitle");
  const routeMeta = document.querySelector("#route-meta");
  const routeSummary = document.querySelector("#route-summary");
  const routeMapBtn = document.querySelector("#route-map-btn");
  const resetBtn = document.querySelector("#reset-btn");
  const progressLabel = document.querySelector("#progress-label");
  const progressBar = document.querySelector("#progress-bar");
  const stopsEl = document.querySelector("#stops");

  let currentRoute = null;

  function visitedKey(slug) {
    return `visited:${slug}`;
  }

  function getVisited(slug) {
    return new Set(JSON.parse(localStorage.getItem(visitedKey(slug)) || "[]"));
  }

  function setVisited(slug, visited) {
    localStorage.setItem(visitedKey(slug), JSON.stringify([...visited].sort((a, b) => a - b)));
  }

  function createRouteButtons() {
    routePicker.innerHTML = "";
    DATA.routes.forEach(route => {
      const link = document.createElement("a");
      link.className = "route-chip";
      link.href = `?route=${encodeURIComponent(route.slug)}`;
      link.textContent = route.title;
      link.addEventListener("click", event => {
        event.preventDefault();
        loadRoute(route.slug);
      });
      if (route.slug === currentRoute.slug) link.classList.add("active");
      routePicker.append(link);
    });
  }

  function updateProgress(route, visited) {
    const total = route.stops.length;
    const done = route.stops.filter(stop => visited.has(stop.id)).length;
    progressLabel.textContent = `${done}/${total} geldialdi bisitatuta`;
    progressBar.style.width = `${(done / total) * 100}%`;
  }

  function toggleVisited(route, stopId, button, card) {
    const visited = getVisited(route.slug);
    if (visited.has(stopId)) {
      visited.delete(stopId);
      button.textContent = "Bisitatuta";
      button.classList.remove("visited");
      card.classList.remove("done");
    } else {
      visited.add(stopId);
      button.textContent = "Bisita egina";
      button.classList.add("visited");
      card.classList.add("done");
    }
    setVisited(route.slug, visited);
    updateProgress(route, visited);
  }

  function attachVideoBehavior(container) {
    const video = container.querySelector("video");
    if (!video) return;

    const hide = () => {
      container.hidden = true;
    };

    video.addEventListener("error", hide, { once: true });
    video.addEventListener("loadeddata", () => {
      container.hidden = false;
    }, { once: true });
  }

  function renderStops(route) {
    const visited = getVisited(route.slug);
    stopsEl.innerHTML = "";

    route.stops.forEach((stop, index) => {
      const card = document.createElement("article");
      card.className = "stop-card";
      if (visited.has(stop.id)) card.classList.add("done");

      const nextButton = index < route.stops.length - 1
        ? `<button class="soft-btn next-stop" type="button" data-next="${index + 1}">Hurrengo geldialdia</button>`
        : "";

      const media = stop.image
        ? `<img class="stop-image" src="${stop.image}" alt="${stop.title}" loading="lazy">`
        : `<div class="stop-image fallback" aria-hidden="true">✦</div>`;

      const visitedLabel = visited.has(stop.id) ? "Bisita egina" : "Bisitatuta";

      card.innerHTML = `
        <div class="stop-top">
          ${media}
          <div class="stop-main">
            <span class="stop-time">${stop.time_rel}</span>
            <h2>${stop.title}</h2>
            <p class="stop-blurb">${stop.blurb}</p>
          </div>
        </div>
        <div class="stop-actions">
          <button class="primary-btn toggle-script" type="button">Irakurri gidoi osoa</button>
          <a class="map-btn" href="${stop.maps_url}" target="_blank" rel="noreferrer">Ireki Google Maps-en</a>
        </div>
        <div class="video-wrap" ${stop.video_exists ? "" : "hidden"}>
          <video controls preload="none" playsinline src="${stop.video_url}"></video>
        </div>
        <div class="stop-script" hidden>
          ${stop.script_html}
        </div>
        <dl class="stop-notes">
          <div>
            <dt>Argazki-aholkua</dt>
            <dd>${stop.photo_tip}</dd>
          </div>
          <div>
            <dt>Xehetasun ezkutua</dt>
            <dd>${stop.hidden_detail}</dd>
          </div>
        </dl>
        <div class="stop-bottom">
          ${nextButton}
          <button class="visit-btn ${visited.has(stop.id) ? "visited" : ""}" type="button">${visitedLabel}</button>
        </div>
      `;

      const scriptButton = card.querySelector(".toggle-script");
      const script = card.querySelector(".stop-script");
      const visitButton = card.querySelector(".visit-btn");
      const videoWrap = card.querySelector(".video-wrap");

      scriptButton.addEventListener("click", () => {
        const isHidden = script.hidden;
        script.hidden = !isHidden;
        scriptButton.textContent = isHidden ? "Gidoia itxi" : "Irakurri gidoi osoa";
      });

      visitButton.addEventListener("click", () => toggleVisited(route, stop.id, visitButton, card));

      card.querySelector(".next-stop")?.addEventListener("click", () => {
        const nextCard = stopsEl.querySelectorAll(".stop-card")[index + 1];
        nextCard?.scrollIntoView({ behavior: "smooth", block: "start" });
      });

      attachVideoBehavior(videoWrap);
      stopsEl.append(card);
    });

    updateProgress(route, visited);
  }

  function loadRoute(slug) {
    const route = DATA.routes.find(item => item.slug === slug) || DATA.routes[0];
    currentRoute = route;

    routeTitle.textContent = route.title;
    routeSubtitle.textContent = route.subtitle;
    routeMeta.textContent = `${route.duration} · ${route.start_label} → ${route.end_label}`;
    routeSummary.textContent = route.summary;
    routeMapBtn.href = route.route_maps_url;
    resetBtn.onclick = () => {
      localStorage.removeItem(visitedKey(route.slug));
      renderStops(route);
    };

    renderStops(route);
    createRouteButtons();

    const url = new URL(window.location.href);
    url.searchParams.set("route", route.slug);
    window.history.replaceState({}, "", url);
  }

  loadRoute(defaultSlug);

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("sw.js"));
  }
})();
