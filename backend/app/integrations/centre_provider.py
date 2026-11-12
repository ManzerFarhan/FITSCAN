"""CentreProvider interface (FR-TEST-5) - swap Google Places / OpenStreetMap / demo without touching services."""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    lat: float
    lng: float
    label: str | None = None


class Centre(BaseModel):
    provider_id: str
    name: str
    address: str | None = None
    locality: str | None = None
    city: str | None = None
    lat: float
    lng: float
    phone: str | None = None
    website: str | None = None
    maps_url: str | None = None
    booking_url: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    hours: list[str] = Field(default_factory=list)
    business_status: str | None = None
    categories: list[str] = Field(default_factory=list)
    listed_services: list[str] = Field(default_factory=list)  # only when the provider actually lists them
    price: str | None = None  # only if reliably sourced; providers here never set it


class ProviderError(RuntimeError):
    pass


class CentreProvider(Protocol):
    name: str

    def geocode(self, query: str) -> GeoPoint | None: ...

    def search(self, test_names: list[str], origin: GeoPoint, radius_km: float, place_label: str) -> list[Centre]: ...
