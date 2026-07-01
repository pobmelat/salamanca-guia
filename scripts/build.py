#!/usr/bin/env python3
"""Eraiki PWAko datuak YAML + Markdown iturrietatik."""

from __future__ import annotations

import html
import json
from urllib.parse import quote
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROUTES_DIR = ROOT / "data" / "routes"
CONTENT_DIR = ROOT / "content" / "eu"
PUBLIC_MEDIA = ROOT / "public" / "media"
PUBLIC_IMAGES = ROOT / "public" / "images"
APP_DIR = ROOT / "app"


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def paragraph(text: str) -> str:
    return f"<p>{html.escape(text)}</p>"


def markdown_to_html(text: str) -> str:
    blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            blocks.append(paragraph(" ".join(paragraph_lines)))
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{html.escape(item)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue

        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h3>{html.escape(line[2:])}</h3>")
            continue

        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h4>{html.escape(line[3:])}</h4>")
            continue

        if line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:])
            continue

        flush_list()
        paragraph_lines.append(line)

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def maps_point_value(point: dict) -> str:
    if point.get("query"):
        return quote(point["query"])
    return f"{point['lat']},{point['lon']}"


def stop_maps_url(stop: dict) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={maps_point_value(stop)}"
        "&travelmode=walking"
    )


def route_maps_url(route: dict) -> str:
    origin = route["google_maps"]["origin"]
    destination = route["google_maps"]["destination"]
    waypoints = route["google_maps"].get("waypoints", [])
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={maps_point_value(origin)}"
        f"&destination={maps_point_value(destination)}"
        "&travelmode=walking"
    )
    if waypoints:
        joined = "|".join(maps_point_value(point) for point in waypoints)
        url += f"&waypoints={joined}"
    return url


def build_route(path: Path) -> tuple[dict, list[str]]:
    route = read_yaml(path)
    slug = route["slug"]
    route_content_dir = CONTENT_DIR / slug
    assets: list[str] = []

    built_stops = []
    for stop in route["stops"]:
        stop_id = int(stop["id"])
        markdown_path = route_content_dir / f"parada{stop_id:02d}.md"
        script_md = markdown_path.read_text(encoding="utf-8")
        image_path = None
        if stop.get("image"):
            image_file = PUBLIC_IMAGES / stop["image"]
            if image_file.exists():
                image_path = f"../public/images/{stop['image']}"
                assets.append(image_path)

        video_rel = f"../public/media/{slug}/parada{stop_id:02d}.mp4"
        video_exists = (PUBLIC_MEDIA / slug / f"parada{stop_id:02d}.mp4").exists()
        if video_exists:
            assets.append(video_rel)

        built_stops.append(
            {
                "id": stop_id,
                "time_rel": stop["time_rel"],
                "title": stop["title"],
                "short": stop["short"],
                "lat": float(stop["lat"]) if stop.get("lat") is not None else None,
                "lon": float(stop["lon"]) if stop.get("lon") is not None else None,
                "blurb": stop["blurb"],
                "seeing": stop.get("seeing"),
                "look_now": stop.get("look_now"),
                "photo_tip": stop["photo_tip"],
                "hidden_detail": stop["hidden_detail"],
                "image": image_path,
                "script_html": markdown_to_html(script_md),
                "script_path": f"../content/eu/{slug}/parada{stop_id:02d}.md",
                "maps_url": stop_maps_url(stop),
                "video_url": video_rel,
                "video_exists": video_exists,
            }
        )

    built_route = {
        "slug": slug,
        "city": route["city"],
        "lang": route["lang"],
        "title": route["title"],
        "subtitle": route["subtitle"],
        "duration": route["duration"],
        "summary": route["summary"],
        "start_label": route["start_label"],
        "end_label": route["end_label"],
        "route_maps_url": route_maps_url(route),
        "stops": built_stops,
    }
    return built_route, assets


def write_data(routes: list[dict]) -> None:
    payload = {
        "app": {
            "title": "Salamanca Guide",
            "tagline": "Google Maps-ek oinak gidatzen ditu. PWAk begirada.",
            "defaultRoute": "dia2_goiza",
        },
        "routes": routes,
    }
    (APP_DIR / "data.js").write_text(
        "window.GUIDE_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def write_service_worker(asset_paths: list[str]) -> None:
    core_assets = [
        "./",
        "index.html",
        "style.css",
        "app.js",
        "data.js",
        "manifest.webmanifest",
        "icon-192.png",
        "icon-512.png",
    ]
    unique_assets = []
    seen = set()
    for item in [*core_assets, *asset_paths]:
        if item not in seen:
            unique_assets.append(item)
            seen.add(item)

    sw = f"""const CACHE = "salamanca-guide-v3";
const ASSETS = {json.dumps(unique_assets, ensure_ascii=False, indent=2)};

self.addEventListener("install", event => {{
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
}});

self.addEventListener("activate", event => {{
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", event => {{
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then(hit => {{
      if (hit) return hit;
      return fetch(event.request)
        .then(response => {{
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, copy));
          return response;
        }})
        .catch(() => caches.match("index.html"));
    }})
  );
}});
"""
    (APP_DIR / "sw.js").write_text(sw, encoding="utf-8")


def main() -> None:
    routes = []
    assets: list[str] = []

    for path in sorted(ROUTES_DIR.glob("*.yaml")):
        route, route_assets = build_route(path)
        routes.append(route)
        assets.extend(route_assets)

    write_data(routes)
    write_service_worker(assets)
    print(f"{len(routes)} ibilbide eguneratu dira.")


if __name__ == "__main__":
    main()
