// frontend/src/components/LiveMap.jsx
import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34]
});
L.Marker.prototype.options.icon = DefaultIcon;

function MapFlyController({ coords }) {
  const map = useMap();
  useEffect(() => {
    if (coords?.lat && coords?.lng) {
      map.flyTo([coords.lat, coords.lng], 13, { animate: true, duration: 1.2 });
    }
  }, [coords, map]);
  return null;
}

export default function LiveMap({ center, competitors = [], siteLabel = "Proposed Business Site" }) {
  return (
    <div className="h-96 w-full rounded-2xl overflow-hidden border border-gray-200 shadow-sm">
      <MapContainer
        center={[center.lat, center.lng]}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapFlyController coords={center} />

        {/* Selected Enterprise Target Marker */}
        <Marker position={[center.lat, center.lng]}>
          <Popup>
            <div className="text-sm">
              <strong className="text-blue-600 block">{siteLabel}</strong>
              <span>Target Point: {center.lat.toFixed(4)}, {center.lng.toFixed(4)}</span>
            </div>
          </Popup>
        </Marker>

        {/* 5 km Saturation Radius */}
        <Circle
          center={[center.lat, center.lng]}
          radius={5000}
          pathOptions={{ color: '#2563eb', fillColor: '#3b82f6', fillOpacity: 0.1, weight: 1.5 }}
        />

        {/* Live Overpass Competitor Markers */}
        {competitors.map((comp) => (
          <Marker key={comp.id} position={[comp.lat, comp.lng]}>
            <Popup>
              <div className="text-xs">
                <strong className="text-red-600 block">{comp.name}</strong>
                <span>Sector: {comp.category}</span>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}