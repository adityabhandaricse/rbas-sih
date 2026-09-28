import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Circle, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix Vite Marker Icons if default icons are used anywhere
import L from "leaflet";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// View controller to dynamically fly to updated GPS/Nominatim coordinates
function MapViewController({ center }) {
  const map = useMap();
  const lastCenterRef = useRef("");

  useEffect(() => {
    if (!center?.lat || (!center?.lon && !center?.lng)) return;

    const lat = center.lat;
    const lon = center.lon ?? center.lng;
    const centerKey = `${lat.toFixed(5)},${lon.toFixed(5)}`;

    // Trigger canvas size recalculation to prevent broken grey tiles
    const resizeTimer = setTimeout(() => {
      map.invalidateSize();
    }, 150);

    // Pan map smoothly only if coordinates actually changed
    if (lastCenterRef.current !== centerKey) {
      lastCenterRef.current = centerKey;
      map.flyTo([lat, lon], 12, {
        animate: true,
        duration: 1.2,
      });
    }

    return () => clearTimeout(resizeTimer);
  }, [center, map]);

  return null;
}

export default function InteractiveMap({ center, competitors = [] }) {
  if (!center?.lat || (!center?.lon && !center?.lng)) return null;

  const lat = center.lat;
  const lon = center.lon ?? center.lng;
  const position = [lat, lon];

  return (
    <div
      className="w-full h-[380px] rounded-xl overflow-hidden border border-paper-dk relative z-0"
      style={{ isolation: "isolate" }}
    >
      <MapContainer
        center={position}
        zoom={12}
        scrollWheelZoom={false} // Prevents page scrolling conflicts
        style={{ height: "100%", width: "100%", zIndex: 0 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Dynamic center sync hook */}
        <MapViewController center={center} />

        {/* 5 km and 10 km Market Catchment Zones */}
        <Circle
          center={position}
          radius={5000}
          pathOptions={{ color: "#3d7a4d", fillColor: "#3d7a4d", fillOpacity: 0.08, weight: 1.5 }}
        />
        <Circle
          center={position}
          radius={10000}
          pathOptions={{
            color: "#b5602c",
            fillColor: "#b5602c",
            fillOpacity: 0.04,
            weight: 1.2,
            dashArray: "4, 4",
          }}
        />

        {/* Selected Enterprise Target Marker */}
        <CircleMarker
          center={position}
          radius={7}
          pathOptions={{ color: "#1e40af", fillColor: "#3b82f6", fillOpacity: 1, weight: 2 }}
        >
          <Popup>
            <div className="text-xs">
              <strong className="block text-gray-900">Proposed Enterprise Location</strong>
              <span className="text-gray-500 font-mono">
                {lat.toFixed(4)}, {lon.toFixed(4)}
              </span>
            </div>
          </Popup>
        </CircleMarker>

        {/* Live Competitor Markers */}
        {competitors.map((c, i) => {
          const cLat = c.lat ?? c.latitude;
          const cLon = c.lon ?? c.lng ?? c.longitude;
          if (!cLat || !cLon) return null;

          return (
            <CircleMarker
              key={c.id ?? c.osm_id ?? i}
              center={[cLat, cLon]}
              radius={5}
              pathOptions={{ color: "#991b1b", fillColor: "#ef4444", fillOpacity: 0.85, weight: 1.5 }}
            >
              <Popup>
                <div className="text-xs space-y-0.5">
                  <strong className="block text-gray-900">{c.name || "Competitor"}</strong>
                  {c.category && <span className="text-gray-500 block">Sector: {c.category}</span>}
                  {c.distance_km && <span className="text-gray-600 block">{c.distance_km} km away</span>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}