"use client";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import type { RankedCentre } from "@/lib/types";
import { directionsUrl } from "./CentreCard";

const pin = (n: number, active: boolean) => L.divIcon({
  className: "",
  html: `<div style="background:${active ? "#115e59" : "#0d9488"};color:#fff;width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)"><span style="transform:rotate(45deg);font:600 12px system-ui">${n}</span></div>`,
  iconSize: [26, 26], iconAnchor: [13, 26], popupAnchor: [0, -24],
});

function Fit({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => { if (points.length) map.fitBounds(L.latLngBounds(points).pad(0.2), { maxZoom: 15 }); }, [map, points]);
  return null;
}

/** FR-TEST-10: Leaflet + OpenStreetMap tiles (no key needed); markers, popups, external navigation. */
export default function CentreMap({ origin, radiusKm, results, activeId, onSelect }: {
  origin: { lat: number; lng: number }; radiusKm: number; results: RankedCentre[]; activeId: string | null; onSelect: (id: string) => void;
}) {
  const points: [number, number][] = [[origin.lat, origin.lng], ...results.map((r) => [r.centre.lat, r.centre.lng] as [number, number])];
  return (
    <MapContainer center={[origin.lat, origin.lng]} zoom={13} scrollWheelZoom={false} className="h-[420px] w-full" aria-label="Map of diagnostic centres">
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Circle center={[origin.lat, origin.lng]} radius={radiusKm * 1000} pathOptions={{ color: "#0d9488", weight: 1, fillOpacity: 0.04 }} />
      {results.map((r, i) => (
        <Marker key={r.centre.provider_id} position={[r.centre.lat, r.centre.lng]} icon={pin(i + 1, r.centre.provider_id === activeId)}
          eventHandlers={{ click: () => onSelect(r.centre.provider_id) }}>
          <Popup>
            <strong>{r.centre.name}</strong><br />
            {r.centre.address ?? ""}<br />
            {r.distance_km !== null && <>{r.distance_km} km · </>}{r.verified ? "Verified listing" : "Unverified listing"}<br />
            <a href={directionsUrl(r.centre.lat, r.centre.lng)} target="_blank" rel="noreferrer">Get directions</a>
          </Popup>
        </Marker>
      ))}
      <Fit points={points} />
    </MapContainer>
  );
}
