"""
seed_categories.py
Run with: python manage.py shell < seed_categories.py
Populates BusinessCategory with the OSM tag sets used by the Overpass queries.
"""
from core.models import BusinessCategory

CATEGORIES = [
    ("Dairy / Milk products", "DAIRY", ["shop=dairy", "shop=farm"], 20.0, 0.6),
    ("Grocery / General store", "GROCERY", ["shop=convenience", "shop=grocery", "shop=general"], 12.0, 0.55),
    ("Tailoring / Boutique", "TAILOR", ["shop=tailor", "shop=clothes"], 35.0, 0.4),
    ("Poultry farming", "POULTRY", ["shop=farm", "craft=butcher"], 17.0, 0.65),
    ("Bakery / Snacks", "BAKERY", ["shop=bakery", "shop=confectionery"], 30.0, 0.5),
    ("Handicraft / Weaving", "HANDICRAFT", ["shop=craft", "shop=gift"], 40.0, 0.3),
    ("Salon / Beauty parlour", "SALON", ["shop=hairdresser", "shop=beauty"], 47.0, 0.45),
    ("Mobile & electronics repair", "ELECTRONICS", ["shop=mobile_phone", "shop=electronics", "craft=electronics_repair"], 25.0, 0.5),
    ("Hardware / Building materials", "HARDWARE", ["shop=hardware", "shop=doityourself"], 15.0, 0.6),
]

for name, code, tags, margin, capex in CATEGORIES:
    BusinessCategory.objects.update_or_create(
        code=code,
        defaults={"name": name, "osm_tags": tags, "typical_margins_percent": margin, "capex_ratio": capex},
    )

print(f"Seeded {len(CATEGORIES)} business categories.")
