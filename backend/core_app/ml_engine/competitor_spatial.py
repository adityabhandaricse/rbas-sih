import numpy as np
from scipy.spatial.distance import pdist

def extract_spatial_density_features(center_lat: float, center_lng: float, competitors: list) -> dict:
    """
    Computes spatial density, nearest competitor distance, and clustering metrics.
    """
    comp_count = len(competitors)
    if comp_count == 0:
        return {
            "competitor_count": 0,
            "min_distance_km": 10.0,
            "avg_distance_km": 10.0,
            "spatial_concentration_index": 0.0,
            "clustering_pattern": "ISOLATED_OPPORTUNITY"
        }

    # Extract coordinates
    coords = []
    for c in competitors:
        lat = c.get("lat") or c.get("latitude")
        lng = c.get("lng") or c.get("lon") or c.get("longitude")
        if lat and lng:
            coords.append([float(lat), float(lng)])

    if not coords:
        return {
            "competitor_count": comp_count,
            "min_distance_km": 5.0,
            "avg_distance_km": 5.0,
            "spatial_concentration_index": 0.5,
            "clustering_pattern": "SPARSE"
        }

    coords_arr = np.array(coords)
    center = np.array([center_lat, center_lng])

    # Convert approx degree differences to km (1 deg lat ~ 111 km, lon ~ 102 km in eastern India)
    lat_diff = (coords_arr[:, 0] - center[0]) * 111.0
    lng_diff = (coords_arr[:, 1] - center[1]) * 102.0
    distances_km = np.sqrt(lat_diff**2 + lng_diff**2)

    min_dist = float(np.min(distances_km))
    avg_dist = float(np.mean(distances_km))

    # Calculate pairwise internal spread
    if comp_count >= 2:
        pairwise_km = pdist(coords_arr) * 110.0
        concentration_index = float(1.0 / (1.0 + np.mean(pairwise_km)))
    else:
        concentration_index = 0.2

    if min_dist < 1.0:
        pattern = "HIGHLY_CENTRALIZED_BAZAAR"
    elif concentration_index > 0.4:
        pattern = "CLUSTER_FORMATION"
    else:
        pattern = "DECENTRALIZED_SCATTERED"

    return {
        "competitor_count": comp_count,
        "min_distance_km": round(min_dist, 2),
        "avg_distance_km": round(avg_dist, 2),
        "spatial_concentration_index": round(concentration_index, 3),
        "clustering_pattern": pattern
    }