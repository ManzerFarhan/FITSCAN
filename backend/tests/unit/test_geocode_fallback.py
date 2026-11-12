"""Geocoding falls back from the full address to simpler forms (landmark + 'New Delhi' vs 'Delhi' case)."""
from app.integrations.centre_provider import GeoPoint, ProviderError
from app.services import centre_service as cs
from app.services.centre_service import LocationOut, geocode_candidates, geocode_location


class Geo:
    name = "fake"

    def __init__(self, known: dict[str, str]):
        self.known, self.calls = known, []

    def geocode(self, q):
        self.calls.append(q)
        label = self.known.get(q.removesuffix(", India").lower())
        return GeoPoint(lat=28.52, lng=77.18, label=label) if label else None


LOC = LocationOut(city="new delhi", locality="qutub minar", postal_code="110030", source="MANUAL")


def test_candidates_most_specific_first():
    qs = [q for q, _ in geocode_candidates(LOC)]
    assert qs == ["qutub minar, new delhi, 110030", "qutub minar, new delhi", "qutub minar, 110030", "qutub minar",
                  "110030", "new delhi"]


def test_landmark_found_when_full_address_is_not():
    p = Geo({"qutub minar": "Qutb Minar, Mehrauli, South Delhi, Delhi, 110030, India"})
    assert geocode_location(p, LOC).label.startswith("Qutb Minar")


def test_area_alone_in_wrong_city_is_rejected():
    loc = LocationOut(city="Pune", locality="MG Road", source="MANUAL")
    p = Geo({"mg road": "MG Road, Bengaluru, Karnataka, India", "pune": "Pune, Maharashtra, India"})
    assert geocode_location(p, loc).label.startswith("Pune")


def test_google_failure_falls_back_to_osm(member, monkeypatch):
    class BrokenGoogle:
        name = "google_places"

        def geocode(self, q):
            raise ProviderError("bad key")

    class OSM:
        name = "openstreetmap"

        def geocode(self, q):
            return GeoPoint(lat=18.52, lng=73.85, label=q)

        def search(self, *a):
            return []

    monkeypatch.setattr(cs, "get_provider", lambda: BrokenGoogle())
    monkeypatch.setattr("app.integrations.osm.OSMProvider", OSM)
    r = member.post("/api/v1/centres/search", json={"city": "Pune"})
    assert r.status_code == 200 and r.json()["provider"] == "openstreetmap"
