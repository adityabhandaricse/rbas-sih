// frontend/src/api/geo.js

const NOMINATIM_BASE = "https://nominatim.openstreetmap.org";
const HEADERS = { "User-Agent": "GramSetu-App/1.0" };

// Forward Geocoding: Village/Block/District -> { lat, lon, displayName }
export async function forwardGeocode({ village, block, district }) {
  // Strategy 1: High precision query
  const specificQuery = [village, block, district, "West Bengal", "India"]
    .filter(Boolean)
    .join(", ");

  try {
    const res = await fetch(
      `${NOMINATIM_BASE}/search?format=json&q=${encodeURIComponent(specificQuery)}&limit=1`,
      { headers: HEADERS }
    );
    const data = await res.json();
    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
        displayName: data[0].display_name
      };
    }
  } catch (err) {
    console.error("Village forward geocode failed:", err);
  }

  // Strategy 2: Fallback to Sub-District / District level if the village wasn't indexed
  const broadQuery = [block || district, district, "West Bengal", "India"]
    .filter(Boolean)
    .join(", ");

  try {
    const fallbackRes = await fetch(
      `${NOMINATIM_BASE}/search?format=json&q=${encodeURIComponent(broadQuery)}&limit=1`,
      { headers: HEADERS }
    );
    const fallbackData = await fallbackRes.json();
    if (fallbackData && fallbackData.length > 0) {
      return {
        lat: parseFloat(fallbackData[0].lat),
        lon: parseFloat(fallbackData[0].lon),
        displayName: fallbackData[0].display_name
      };
    }
  } catch (err) {
    console.error("District fallback geocode failed:", err);
  }

  return null;
}

// Reverse Geocoding: GPS (lat, lon) -> { village, block, district, addressLine }
export async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(
      `${NOMINATIM_BASE}/reverse?format=json&lat=${lat}&lon=${lon}&zoom=14&addressdetails=1`,
      { headers: HEADERS }
    );
    const data = await res.json();
    const addr = data.address || {};

    return {
      village: addr.village || addr.hamlet || addr.suburb || addr.town || addr.city || "",
      block: addr.county || addr.subdistrict || "",
      district: addr.state_district || addr.district || addr.city || "",
      displayName: data.display_name || ""
    };
  } catch (err) {
    console.error("Reverse geocoding failed:", err);
    return null;
  }
}