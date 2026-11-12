"""OpenStreetMap provider (Nominatim geocoding + Overpass) - keyless fallback (A2).
Respects the OSMF usage policies: identifying User-Agent, low volume, results cached by centre_service."""
from __future__ import annotations

import time
from urllib.parse import quote_plus

import httpx

from app.integrations.centre_provider import Centre, GeoPoint, ProviderError

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "FITSCAN-prototype/0.2 (educational diagnostic-centre finder)"}
KEYWORDS = ["diagnostic", "laboratory", "clinic", "hospital"]
EXCLUDE_WORDS = ("forensic", "veterinary", "pet ", "animal")


def google_maps_url(name: str, address: str | None) -> str:
    """Open the centre in Google Maps (no key needed for a search link)."""
    text = address if address and address.lower().startswith(name.lower()) else ", ".join(x for x in (name, address) if x)
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(text)


class OSMProvider:
    name = "openstreetmap"

    def __init__(self, timeout: float = 25.0):
        self.http = httpx.Client(timeout=timeout, headers=HEADERS)

    def geocode(self, query: str) -> GeoPoint | None:
        try:
            r = self.http.get(NOMINATIM, params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "in"})
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError("Geocoding failed") from exc
        data = r.json()
        if not data:
            return None
        return GeoPoint(lat=float(data[0]["lat"]), lng=float(data[0]["lon"]), label=data[0].get("display_name"))

    def search(self, test_names: list[str], origin: GeoPoint, radius_km: float, place_label: str) -> list[Centre]:
        rad = int(min(radius_km, 25) * 1000)
        a = f"(around:{rad},{origin.lat},{origin.lng})"
        q = f"""[out:json][timeout:20];
(
  nwr["healthcare"~"laboratory|clinic|hospital|centre"]{a};
  nwr["amenity"~"clinic|hospital"]{a};
);
out center tags 80;"""
        try:
            r = self.http.post(OVERPASS, data={"data": q}, timeout=12.0)
            r.raise_for_status()
            r.json()
        except (httpx.HTTPError, ValueError):
            return self._nominatim_search(origin, radius_km)  # Overpass is often overloaded
        out = []
        for el in r.json().get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name")
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lng = el.get("lon") or el.get("center", {}).get("lon")
            if not name or lat is None:
                continue
            addr = ", ".join(x for x in [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:suburb"),
                                         tags.get("addr:city"), tags.get("addr:postcode")] if x) or None
            out.append(Centre(
                provider_id=f"osm:{el['type']}/{el['id']}", name=name, address=addr, locality=tags.get("addr:suburb"),
                city=tags.get("addr:city"), lat=float(lat), lng=float(lng),
                phone=tags.get("phone") or tags.get("contact:phone"), website=tags.get("website") or tags.get("contact:website"),
                maps_url=google_maps_url(name, addr or tags.get("addr:city")),
                hours=[tags["opening_hours"]] if tags.get("opening_hours") else [],
                categories=[v for k, v in tags.items() if k in ("healthcare", "amenity", "healthcare:speciality")],
            ))
        return out

    def _nominatim_search(self, origin: GeoPoint, radius_km: float) -> list[Centre]:
        """Fallback: bounded keyword search on Nominatim (max 1 request/second per the usage policy)."""
        d = min(radius_km, 25) / 111.0
        viewbox = f"{origin.lng - d},{origin.lat + d},{origin.lng + d},{origin.lat - d}"
        seen: dict[str, Centre] = {}
        ok = False
        for i, kw in enumerate(KEYWORDS):
            if i:
                time.sleep(1.05)
            try:
                r = self.http.get(NOMINATIM, params={"q": kw, "format": "jsonv2", "limit": 20, "bounded": 1, "viewbox": viewbox,
                                                     "extratags": 1, "addressdetails": 1})
                r.raise_for_status()
                ok = True
            except httpx.HTTPError:
                continue
            for x in r.json():
                if x.get("category") not in ("amenity", "healthcare") or not x.get("name"):
                    continue
                if any(w in x["name"].lower() for w in EXCLUDE_WORDS):
                    continue
                pid = f"osm:{x.get('osm_type')}/{x.get('osm_id')}"
                tags, addr = x.get("extratags") or {}, x.get("address") or {}
                seen.setdefault(pid, Centre(
                    provider_id=pid, name=x["name"], address=x.get("display_name"),
                    locality=addr.get("suburb") or addr.get("neighbourhood"), city=addr.get("city") or addr.get("town"),
                    lat=float(x["lat"]), lng=float(x["lon"]), phone=tags.get("phone") or tags.get("contact:phone"),
                    website=tags.get("website") or tags.get("contact:website"),
                    maps_url=google_maps_url(x["name"], x.get("display_name")),
                    hours=[tags["opening_hours"]] if tags.get("opening_hours") else [], categories=[x.get("type", "")],
                ))
        if not ok:
            raise ProviderError("OpenStreetMap search failed")
        return list(seen.values())
