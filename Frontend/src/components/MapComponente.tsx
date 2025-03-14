"use client"; // Sicherstellen, dass die Komponente nur im Client läuft

import { useRef, useEffect, useState } from "react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";

export default function MapComponent({ position }) {
  const mapRef = useRef<L.Map | null>(null);
  const [customIcon, setCustomIcon] = useState<L.Icon | null>(null);

  useEffect(() => {
    const icon = L.icon({
      iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
      shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
      iconSize: [25, 41],
      iconAnchor: [12, 41],
    });
    setCustomIcon(icon);
  }, []);

  if (!customIcon) return <p>Lade Karte...</p>;

  return (
    <div className="w-full h-[500px]">
      <MapContainer center={position} zoom={13} className="w-full h-full" whenCreated={(map) => (mapRef.current = map)}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={position} icon={customIcon}>
          <Popup>Selected Location</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
