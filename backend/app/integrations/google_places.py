"""Google Places API (New) provider (P3-17). Server-side only - the key never reaches the browser."""
from __future__ import annotations

import httpx

from app.integrations.centre_provider import Centre, GeoPoint, ProviderError

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.location", "places.rating",
    "places.userRatingCount", "places.nationalPhoneNumber", "places.internationalPhoneNumber", "places.websiteUri",
    "places.regularOpeningHours.weekdayDescriptions", "places.businessStatus", "places.types", "places.googleMapsUri",
    "places.addressComponents",
])


class GooglePlacesProvider:
    name = "google_places"

    def __init__(self, api_key: str, timeout: float = 12.0):
        self.api_key = api_key
        self.http = httpx.Client(timeout=timeout)

    def _search_text(self, query: str, bias: GeoPoint | None = None, radius_km: float = 10, limit: int = 20) -> list[dict]:
        body: dict = {"textQuery": query, "maxResultCount": limit, "languageCode": "en", "regionCode": "IN"}
        if bias:
            body["locationBias"] = {"circle": {"center": {"latitude": bias.lat, "longitude": bias.lng},
                                               "radius": min(radius_km * 1000, 50000)}}
        try:
            r = self.http.post(SEARCH_URL, json=body, headers={"X-Goog-Api-Key": self.api_key, "X-Goog-FieldMask": FIELD_MASK})
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError("Google Places request failed") from exc
        return r.json().get("places", [])

    def geocode(self, query: str) -> GeoPoint | None:
        places = self._search_text(query, limit=1)
        if not places:
            return None
        loc = places[0]["location"]
        return GeoPoint(lat=loc["latitude"], lng=loc["longitude"], label=places[0].get("formattedAddress"))

    def search(self, test_names: list[str], origin: GeoPoint, radius_km: float, place_label: str) -> list[Centre]:
        seen: dict[str, Centre] = {}
        queries = [f"diagnostic lab pathology near {place_label}"] + [f"{t} test lab near {place_label}" for t in test_names[:2]]
        for q in queries:
            for p in self._search_text(q, origin, radius_km):
                if p["id"] in seen:
                    continue
                comps = {t: c.get("longText") for c in p.get("addressComponents", []) for t in c.get("types", [])}
                seen[p["id"]] = Centre(
                    provider_id=p["id"], name=p.get("displayName", {}).get("text", "Unnamed"),
                    address=p.get("formattedAddress"), locality=comps.get("sublocality_level_1") or comps.get("sublocality"),
                    city=comps.get("locality"), lat=p["location"]["latitude"], lng=p["location"]["longitude"],
                    phone=p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber"), website=p.get("websiteUri"),
                    maps_url=p.get("googleMapsUri"), rating=p.get("rating"), rating_count=p.get("userRatingCount"),
                    hours=p.get("regularOpeningHours", {}).get("weekdayDescriptions", []),
                    business_status=p.get("businessStatus"), categories=p.get("types", []),
                )
        return list(seen.values())
