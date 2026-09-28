"""
geo_services.py
Client-side helper for the /api/v1/geo/competitors-density/ endpoint.
Queries OpenStreetMap's Overpass API — zero cost, no key required.
"""
import requests
from .calculators import haversine_km, saturation_index

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT_S = 25


def build_overpass_query(lat: float, lon: float, radius_m: int, osm_tags: list[str]) -> str:
    clauses = []
    for tag in osm_tags:
        key, _, value = tag.partition("=")
        clauses.append(f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});')
        clauses.append(f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});')
    body = "".join(clauses)
    return f"[out:json][timeout:{TIMEOUT_S}];({body});out center 100;"


def fetch_competitors(lat: float, lon: float, radius_km: float, osm_tags: list[str]) -> list[dict]:
    query = build_overpass_query(lat, lon, int(radius_km * 1000), osm_tags)
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=TIMEOUT_S)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    results = []
    for el in elements:
        el_lat = el.get("lat") or el.get("center", {}).get("lat")
        el_lon = el.get("lon") or el.get("center", {}).get("lon")
        if el_lat is None or el_lon is None:
            continue
        results.append({
            "osm_id": el.get("id"),
            "name": el.get("tags", {}).get("name", "Unnamed business"),
            "lat": el_lat,
            "lon": el_lon,
            "distance_km": round(haversine_km(lat, lon, el_lat, el_lon), 3),
        })
    return results


def competitor_density_report(lat: float, lon: float, osm_tags: list[str]) -> dict:
    """Matches the response contract of POST /api/v1/geo/competitors-density/"""
    all_within_10 = fetch_competitors(lat, lon, 10, osm_tags)
    within_5 = [c for c in all_within_10 if c["distance_km"] <= 5]

    return {
        "competitor_count_5km": len(within_5),
        "competitor_count_10km": len(all_within_10),
        "saturation_5km": saturation_index(len(within_5), 5),
        "saturation_10km": saturation_index(len(all_within_10), 10),
        "competitors": all_within_10,
    }
