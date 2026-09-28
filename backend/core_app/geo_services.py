# backend/core_app/geo_services.py
import requests

OSM_CATEGORY_TAGS = {
    "poultry": '["amenity"~"veterinary|marketplace"]["animal"~"poultry|chicken"]',
    "dairy": '["shop"~"dairy|farm"]["produce"~"milk"]',
    "grocery": '["shop"~"convenience|supermarket|general"]',
    "fertilizer": '["shop"~"agrarian|chemist|farm"]',
    "handicraft": '["shop"~"craft|artisan|gift"]',
    "default": '["shop"]'
}

def fetch_live_competitors(lat, lng, business_type, radius_meters=5000):
    tag = OSM_CATEGORY_TAGS.get(business_type.lower(), OSM_CATEGORY_TAGS["default"])
    query = f"""
    [out:json][timeout:15];
    (
      node{tag}(around:{radius_meters},{lat},{lng});
      way{tag}(around:{radius_meters},{lat},{lng});
    );
    out center;
    """
    url = "https://overpass-api.de/api/interpreter"
    
    try:
        response = requests.post(url, data={'data': query}, headers={'User-Agent': 'GramSetu-Live-App'}, timeout=10)
        if response.status_code == 200:
            data = response.json().get('elements', [])
            competitors = []
            for item in data:
                coords = [item.get('lat') or item.get('center', {}).get('lat'),
                          item.get('lon') or item.get('center', {}).get('lon')]
                if coords[0] and coords[1]:
                    name = item.get('tags', {}).get('name', f"Nearby {business_type.capitalize()} Entity")
                    competitors.append({
                        "id": item['id'],
                        "name": name,
                        "lat": coords[0],
                        "lng": coords[1],
                        "category": business_type
                    })
            
            density_rating = "Low" if len(competitors) < 3 else "Moderate" if len(competitors) < 8 else "High"
            return {
                "competitor_count": len(competitors),
                "density_rating": density_rating,
                "competitors": competitors
            }
    except Exception as e:
        print(f"Overpass query failed: {e}")
        
    return {"competitor_count": 0, "density_rating": "Zero Recorded", "competitors": []}