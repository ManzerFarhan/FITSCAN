"""CentreProvider interface (FR-TEST-5) - swap Google Places / OpenStreetMap / demo without touching services."""
from __future__ import annotations

import re
from typing import NamedTuple, Protocol

from pydantic import BaseModel, Field

from app.core.constants import DoctorType


class DoctorInfo(NamedTuple):
    label: str                     # shown to the user
    query: str                     # what people type into a map search
    osm: tuple[str, ...]           # OpenStreetMap healthcare:speciality values
    words: tuple[str, ...]         # name fragments (matched at word starts) when the speciality isn't tagged


DOCTOR_TYPES: dict[DoctorType, DoctorInfo] = {
    DoctorType.GENERAL_PHYSICIAN: DoctorInfo("General Physician", "general physician", ("general", "internal"),
                                             ("general physician", "family physician", "family doctor", "physician", "internal medicine")),
    DoctorType.PHYSIOTHERAPIST: DoctorInfo("Physiotherapist", "physiotherapist", ("physiotherapy",), ("physio",)),
    DoctorType.CARDIOLOGIST: DoctorInfo("Cardiologist (heart)", "cardiologist", ("cardiology",), ("cardio", "heart")),
    DoctorType.ENDOCRINOLOGIST: DoctorInfo("Endocrinologist (hormones & thyroid)", "endocrinologist", ("endocrinology",),
                                           ("endocrin", "thyroid", "hormone")),
    DoctorType.DIABETOLOGIST: DoctorInfo("Diabetologist (diabetes)", "diabetologist", ("diabetology",), ("diabet", "sugar clinic")),
    DoctorType.DERMATOLOGIST: DoctorInfo("Dermatologist (skin)", "dermatologist", ("dermatology",), ("derma", "skin")),
    DoctorType.GASTROENTEROLOGIST: DoctorInfo("Gastroenterologist (stomach & liver)", "gastroenterologist",
                                              ("gastroenterology", "hepatology"), ("gastro", "digestive", "liver")),
    DoctorType.NEPHROLOGIST: DoctorInfo("Nephrologist (kidney)", "nephrologist", ("nephrology",), ("nephro", "kidney", "dialysis")),
    DoctorType.NEUROLOGIST: DoctorInfo("Neurologist (brain & nerves)", "neurologist", ("neurology",), ("neuro", "brain")),
    DoctorType.ORTHOPAEDIC: DoctorInfo("Orthopaedic (bones & joints)", "orthopaedic doctor", ("orthopaedics", "orthopedics"),
                                       ("ortho", "bone", "joint", "spine")),
    DoctorType.GYNAECOLOGIST: DoctorInfo("Gynaecologist", "gynaecologist", ("gynaecology", "gynecology", "obstetrics"),
                                         ("gynae", "gyne", "gyno", "maternity", "women")),
    DoctorType.PAEDIATRICIAN: DoctorInfo("Paediatrician (children)", "paediatrician", ("paediatrics", "pediatrics"),
                                         ("paediatric", "pediatric", "child", "kids")),
    DoctorType.ENT: DoctorInfo("ENT (ear, nose & throat)", "ENT specialist", ("otolaryngology", "otorhinolaryngology"),
                               ("ent hospital", "ent clinic", "ent care", "ent centre", "e.n.t", "ear nose", "ear, nose")),
    DoctorType.OPHTHALMOLOGIST: DoctorInfo("Eye specialist", "eye specialist", ("ophthalmology",),
                                           ("eye", "ophthalm", "netralaya", "vision")),
    DoctorType.DENTIST: DoctorInfo("Dentist", "dentist", ("dentistry", "dental"), ("dental", "dentist", "teeth", "tooth")),
    DoctorType.PSYCHIATRIST: DoctorInfo("Psychiatrist (mental health)", "psychiatrist", ("psychiatry",),
                                        ("psychiatr", "mental health", "mind")),
    DoctorType.PULMONOLOGIST: DoctorInfo("Pulmonologist (lungs)", "pulmonologist", ("pulmonology", "pneumology"),
                                         ("pulmo", "chest", "lung", "respiratory")),
    DoctorType.UROLOGIST: DoctorInfo("Urologist", "urologist", ("urology",), ("urolog", "uro care", "uro clinic")),
    DoctorType.ONCOLOGIST: DoctorInfo("Oncologist (cancer)", "oncologist", ("oncology",), ("onco", "cancer")),
    DoctorType.HAEMATOLOGIST: DoctorInfo("Haematologist (blood)", "haematologist", ("haematology", "hematology"),
                                         ("haemato", "hemato")),
    DoctorType.DIETITIAN: DoctorInfo("Dietitian / Nutritionist", "dietitian nutritionist", ("dietetics", "nutrition"),
                                     ("diet", "nutrition")),
}


def matches_doctor_type(doctor: DoctorType, name: str, categories: list[str]) -> bool:
    """True when the place is tagged with the speciality or its name says so (word-start match: 'ortho' yes,
    'neuro' does not count for 'uro')."""
    info = DOCTOR_TYPES[doctor]
    tags = " ".join(categories).lower()
    if any(s in tags for s in info.osm):
        return True
    text = f" {name.lower()} "
    return any(re.search(rf"(?<![a-z]){re.escape(w)}", text) for w in info.words)


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
    kind: str = "lab"  # "lab" (tests) | "doctor" (the type of doctor the user picked)


class ProviderError(RuntimeError):
    pass


class CentreProvider(Protocol):
    name: str

    def geocode(self, query: str) -> GeoPoint | None: ...

    def search(self, test_names: list[str], origin: GeoPoint, radius_km: float, place_label: str) -> list[Centre]: ...

    def search_doctors(self, doctor: DoctorType, origin: GeoPoint, radius_km: float, place_label: str) -> list[Centre]: ...
