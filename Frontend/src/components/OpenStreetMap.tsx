"use client"; // Next.js soll das nur im Client rendern

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

const MapComponent = dynamic(() => import("@/components/MapComponente"), { ssr: false });

export default function OpenStreetMap({ address = "Porschestraße 2c Wolfsburg" }) {
  const [position, setPosition] = useState([52.42, 10.785]);

  useEffect(() => {
    const fetchCoordinates = async () => {
      if (!address) return;

      const apiKey = "e6ae3cdfdfad495a8b90c2f70642f652"; // Setze hier deinen Geoapify API-Schlüssel ein

      try {
        const response = await fetch(
          `https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(address)}&apiKey=${apiKey}`
        );
        const data = await response.json();

        if (data.features.length > 0) {
          const { lat, lon } = data.features[0].properties;
          setPosition([lat, lon]);
        } else {
          console.error("Adresse konnte nicht gefunden werden.");
        }
      } catch (error) {
        console.error("Error während der Bearbeitung der Koordinaten", error);
      }
    };

    fetchCoordinates();
  }, [address]);

  return (
    <div className="w-full h-full flex flex-col items-center gap-4 p-4">
      <MapComponent position={position} />
    </div>
  );
}


//e6ae3cdfdfad495a8b90c2f70642f652