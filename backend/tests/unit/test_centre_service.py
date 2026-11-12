"""FR-TEST-8 ranking, BR-06 (lab address never used as patient location), BR-12 verified labels."""

from app.integrations.centre_provider import Centre, GeoPoint
from app.services.centre_service import haversine_km, rank, verification

ORIGIN = GeoPoint(lat=18.52, lng=73.85)


def C(name, lat, lng, **kw):
    return Centre(provider_id=name, name=name, lat=lat, lng=lng, **kw)


def test_haversine():
    assert 0.9 < haversine_km(ORIGIN, 18.529, 73.85) < 1.1


def test_ranking_prefers_nearby_complete_labs():
    near_lab = C("City Diagnostics Lab", 18.522, 73.851, phone="1", website="w", hours=["Mon"], address="a", rating=4.5, rating_count=200)
    far_lab = C("Remote Pathology", 18.60, 73.85, phone="1")
    near_shop = C("Corner Store", 18.5205, 73.8505)
    out = rank([far_lab, near_shop, near_lab], ["Lipid Profile"], ORIGIN, 10, "openstreetmap")
    assert [r.centre.name for r in out][0] == "City Diagnostics Lab"
    assert out[0].score_breakdown["availability"] > out[-1].score_breakdown["availability"]
    assert all(0 <= r.score <= 1 for r in out)


def test_far_and_closed_results_dropped():
    out = rank([C("Lab", 19.5, 73.85), C("Closed Lab", 18.521, 73.85, business_status="CLOSED_PERMANENTLY")],
               ["CBC"], ORIGIN, 10, "google_places")
    assert out == []


def test_verified_only_when_adequately_sourced():  # BR-12
    ok = C("Lab", 1, 1, phone="1", address="a", business_status="OPERATIONAL")
    assert verification(ok, "google_places")[0] is True
    assert verification(ok, "openstreetmap")[0] is False
    assert verification(C("Lab", 1, 1, business_status="OPERATIONAL"), "google_places")[0] is False

