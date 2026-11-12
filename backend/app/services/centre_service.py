"""Centre discovery (FR-TEST-3..11, BR-06, BR-07, BR-12; P3-18..20)."""
from __future__ import annotations

import logging
import math
import re
import time
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import CentreSearch, Document
from app.integrations.centre_provider import Centre, CentreProvider, GeoPoint, ProviderError
from app.services import audit

log = logging.getLogger(__name__)

DISCLAIMER = ("Listings come from public map data and do not guarantee that a test is offered, its price or "
              "availability. Please call the centre to confirm before visiting.")
_LAB_WORDS = ("diagnostic", "pathology", "path lab", "laboratory", "labs", " lab", "lab ", "blood test", "collection centre", "imaging", "scan")
_HOSPITAL_WORDS = ("hospital", "clinic", "medical", "health", "nursing home", "polyclinic")
_CACHE: dict[str, tuple[float, list[Centre]]] = {}
CACHE_TTL = 6 * 3600


class LocationOut(BaseModel):
    city: str | None = None
    locality: str | None = None
    postal_code: str | None = None
    source: str | None = None  # MANUAL | PROFILE | DOCUMENT_PATIENT_ADDRESS
    note: str | None = None


class SearchRequest(BaseModel):
    # Tests the user chose (e.g. from their verified lab report); optional - empty = any diagnostic centre.
    test_names: list[str] = Field(default_factory=list, max_length=10)
    city: str | None = None
    locality: str | None = None
    postal_code: str | None = None
    radius_km: float | None = Field(None, gt=0, le=50)
    lat: float | None = None
    lng: float | None = None


class RankedCentre(BaseModel):
    centre: Centre
    distance_km: float | None
    score: float
    score_breakdown: dict[str, float]
    verified: bool
    verification_note: str
    test_availability: str


@lru_cache
def weights() -> dict:
    return yaml.safe_load((get_settings().config_dir / "ranking_weights.yaml").read_text(encoding="utf-8"))


_provider_override: CentreProvider | None = None


def geocode_candidates(loc: LocationOut) -> list[tuple[str, bool]]:
    """Most specific first. People mix landmarks, areas, PIN codes and 'New Delhi' vs 'Delhi', and a geocoder
    can miss the full combination while finding each part. Returns (query, needs_check) pairs; an area searched
    on its own must land in the right city/PIN (needs_check) - 'MG Road' exists in many cities."""
    city, area, pin = ((x or "").strip() for x in (loc.city, loc.locality, loc.postal_code))
    raw = [
        (", ".join(x for x in (area, city, pin) if x), False),
        (", ".join(x for x in (area, city) if x), False),
        (f"{area}, {pin}" if area and pin else "", False),
        (area, bool(city or pin)),
        (pin, False),
        (city, False),
    ]
    out: list[tuple[str, bool]] = []
    for q, check in raw:
        if q and q.lower() not in {x[0].lower() for x in out}:
            out.append((q, check))
    return out


def _matches_place(point: GeoPoint, loc: LocationOut) -> bool:
    label = (point.label or "").lower()
    if loc.postal_code and loc.postal_code.strip() in label:
        return True
    words = [w for w in re.findall(r"[a-z]+", (loc.city or "").lower()) if len(w) > 3 and w not in ("city", "district")]
    return any(w in label for w in words)


def geocode_location(provider: CentreProvider, loc: LocationOut) -> GeoPoint | None:
    for i, (q, needs_check) in enumerate(geocode_candidates(loc)):
        if i and provider.name == "openstreetmap":
            time.sleep(1.05)  # Nominatim usage policy: max 1 request/second
        point = provider.geocode(q + ", India")
        if point and (not needs_check or _matches_place(point, loc)):
            return point
    return None


def set_provider(p: CentreProvider | None) -> None:  # tests / demos
    global _provider_override
    _provider_override = p


def get_provider() -> CentreProvider:
    if _provider_override is not None:
        return _provider_override
    s = get_settings()
    if s.centre_provider == "google" and s.google_places_api_key:
        from app.integrations.google_places import GooglePlacesProvider

        return GooglePlacesProvider(s.google_places_api_key)
    from app.integrations.osm import OSMProvider

    return OSMProvider()


# ---------------------------------------------------------------- location (FR-TEST-3, BR-06)
def resolve_location(db: Session, owner) -> LocationOut:
    if owner.user and owner.user.preferred_city:
        return LocationOut(city=owner.user.preferred_city, source="PROFILE")
    # BR-06: ONLY an explicitly labelled patient address; the lab's address is never used.
    doc = db.scalars(owner.scope(select(Document), Document).where(Document.patient_address.is_not(None))
                     .order_by(Document.uploaded_at.desc()).limit(1)).first()
    if doc:
        return LocationOut(locality=doc.patient_address, source="DOCUMENT_PATIENT_ADDRESS",
                           note="Taken from the patient address on your report. You can change it.")
    return LocationOut(note="Enter your city or area to search.")


# ---------------------------------------------------------------- ranking (FR-TEST-8)
def haversine_km(a: GeoPoint, b_lat: float, b_lng: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(a.lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lng - a.lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def availability_score(c: Centre, test_names: list[str]) -> tuple[float, str]:
    if c.listed_services and any(t.lower() in " ".join(c.listed_services).lower() for t in test_names):
        return 1.0, "LISTED_BY_PROVIDER"
    text = f" {c.name.lower()} {' '.join(c.categories).lower().replace('_', ' ')} "
    if any(w in text for w in _LAB_WORDS):
        return 0.75, "LIKELY_LAB"
    if any(w in text for w in _HOSPITAL_WORDS):
        return 0.45, "HOSPITAL_OR_CLINIC"
    return 0.2, "UNKNOWN"


def completeness_score(c: Centre) -> float:
    fields = [c.phone, c.website, c.hours, c.address, c.rating]
    return sum(1 for f in fields if f) / len(fields)


def rating_score(c: Centre) -> float:
    if c.rating is None:
        return 0.0
    damp = min(1.0, math.log1p(c.rating_count or 0) / math.log1p(100))
    return (c.rating / 5.0) * damp


def convenience_score(c: Centre) -> float:
    return min(1.0, (0.5 if c.hours else 0) + (0.3 if c.booking_url or c.website else 0) + (0.2 if c.phone else 0))


def verification(c: Centre, provider: str) -> tuple[bool, str]:
    """BR-12: 'verified' only when adequately sourced: operational per the provider + phone + address."""
    if provider == "google_places" and c.business_status == "OPERATIONAL" and c.phone and c.address:
        return True, "Listed as operating on Google Maps with phone and address."
    return False, "Unverified listing - details may be incomplete or out of date."


def rank(centres: list[Centre], test_names: list[str], origin: GeoPoint | None, radius_km: float, provider: str) -> list[RankedCentre]:
    w = weights()["weights"]
    out = []
    for c in centres:
        if c.business_status in ("CLOSED_PERMANENTLY",):
            continue
        dist = haversine_km(origin, c.lat, c.lng) if origin else None
        if dist is not None and dist > radius_km * 1.5:
            continue
        avail, avail_kind = availability_score(c, test_names)
        parts = {
            "availability": avail,
            "proximity": max(0.0, 1 - dist / radius_km) if dist is not None else 0.5,
            "completeness": completeness_score(c),
            "ratings": rating_score(c),
            "convenience": convenience_score(c),
        }
        score = sum(w[k] * v for k, v in parts.items())
        verified, note = verification(c, provider)
        out.append(RankedCentre(
            centre=c, distance_km=round(dist, 2) if dist is not None else None, score=round(score, 4),
            score_breakdown={k: round(v, 3) for k, v in parts.items()}, verified=verified, verification_note=note,
            test_availability={"LISTED_BY_PROVIDER": "Listed by the provider - confirm by phone",
                               "LIKELY_LAB": "Likely offers lab tests - not confirmed",
                               "HOSPITAL_OR_CLINIC": "Hospital/clinic - may offer tests, not confirmed",
                               "UNKNOWN": "Unknown - please confirm"}[avail_kind],
        ))
    out.sort(key=lambda r: r.score, reverse=True)
    return out[: weights().get("max_results", 15)]


# ---------------------------------------------------------------- search (API-13)
def search(db: Session, owner, req: SearchRequest) -> dict:
    radius = req.radius_km or weights().get("default_radius_km", 10)
    if req.city or req.locality or req.postal_code:
        loc = LocationOut(city=req.city, locality=req.locality, postal_code=req.postal_code, source="MANUAL")
    else:
        loc = resolve_location(db, owner)
    label = ", ".join(x for x in [loc.locality, loc.city, loc.postal_code] if x)
    if not label and req.lat is None:
        raise AppError("LOCATION_REQUIRED", "Please enter a city or area to search near.", 422)
    # BR-07: only test names the user picked themselves.
    test_names = sorted({" ".join(t.split())[:80] for t in req.test_names if t and t.strip()})

    primary = get_provider()
    providers = [primary]
    if _provider_override is None and primary.name != "openstreetmap":
        from app.integrations.osm import OSMProvider

        providers.append(OSMProvider())  # e.g. Google key invalid / quota exceeded -> still answer
    origin = centres = provider = None
    for provider in providers:
        try:
            origin = GeoPoint(lat=req.lat, lng=req.lng, label="Your location") if req.lat is not None and req.lng is not None \
                else geocode_location(provider, loc)
            if origin is None:
                raise AppError("LOCATION_NOT_FOUND", "We couldn't find that place. Try the PIN code, a nearby landmark or "
                               "just the city name.", 404)
            key = f"{provider.name}|{round(origin.lat, 3)}|{round(origin.lng, 3)}|{radius}|{'/'.join(test_names)}"
            cached = _CACHE.get(key)
            if cached and time.time() - cached[0] < CACHE_TTL:
                centres = cached[1]
            else:
                centres = provider.search(test_names, origin, radius, label or "you")
                _CACHE[key] = (time.time(), centres)
            break
        except ProviderError:
            log.warning("centre provider %s failed; trying the next one", provider.name)
            continue
    if centres is None or origin is None:
        raise AppError("PROVIDER_UNAVAILABLE", "Centre search is unavailable right now. Please try again in a moment.", 503)

    ranked = rank(centres, test_names, origin, radius, provider.name)
    payload = {
        "location": loc.model_dump(), "origin": origin.model_dump(), "radius_km": radius, "tests": test_names,
        "provider": provider.name, "disclaimer": DISCLAIMER,
        "results": [r.model_dump() for r in ranked],
    }
    db.add(CentreSearch(city=loc.city, locality=loc.locality,
                        query_json={"tests": test_names, "radius_km": radius, "label": label},
                        results_json=[x["centre"]["provider_id"] for x in payload["results"]]))
    audit.record(db, owner, "CENTRE_SEARCH", "centre", None,
                 f"Searched centres for {', '.join(test_names) or 'any diagnostic test'}")
    return payload
