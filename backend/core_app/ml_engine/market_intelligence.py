import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve backend/data_store directory relative to this file
CURRENT_DIR = Path(__file__).resolve().parent
DATA_STORE_DIR = CURRENT_DIR.parent.parent / "data_store"

# Category normalization lookup for standard rural enterprise codes
CATEGORY_MAP = {
    "DAIRY": "DAIRY",
    "MILK": "DAIRY",
    "GROCERY": "GROCERY",
    "GENERAL STORE": "GROCERY",
    "POULTRY": "POULTRY",
    "TAILOR": "TAILOR",
    "BOUTIQUE": "TAILOR",
    "BAKERY": "BAKERY",
    "SNACKS": "BAKERY",
    "HANDICRAFT": "HANDICRAFT",
    "WEAVING": "HANDICRAFT",
    "SALON": "SALON",
    "BEAUTY": "SALON",
    "ELECTRONICS": "ELECTRONICS",
    "MOBILE": "ELECTRONICS",
    "HARDWARE": "HARDWARE",
    "BUILDING": "HARDWARE",
}


def _normalize_category(raw_category: str) -> str:
    """Extracts standard uppercase key from raw category strings."""
    if not raw_category:
        return "GROCERY"
    
    clean_upper = str(raw_category).strip().upper()
    for key, normalized in CATEGORY_MAP.items():
        if key in clean_upper:
            return normalized
    return "GROCERY"


def _load_json_data(filename: str) -> dict:
    """Safely loads a reference JSON file from backend/data_store/."""
    filepath = DATA_STORE_DIR / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ML DataStore Error] File not found: {filepath}")
        logger.error(f"[ML DataStore Error] File not found: {filepath}")
        return {}
    except Exception as e:
        print(f"[ML DataStore Error] Failed to parse {filepath}: {e}")
        logger.error(f"[ML DataStore Error] Failed to parse {filepath}: {e}")
        return {}


def analyze_market_conditions(category: str, district: str = "default") -> dict:
    """
    Computes tax liabilities, regional demand index, and wholesale purchase dynamics.
    """
    cat_key = _normalize_category(category)

    # 1. Tax & Regulatory Slabs
    tax_data = _load_json_data("gst_tax_slabs.json")
    taxes = tax_data.get(cat_key, {
        "category_name": cat_key.capitalize(),
        "hsn_sac": "9999",
        "gst_rate_pct": 5.0,
        "input_tax_credit_eligible": True,
        "composition_scheme_eligible": True,
        "composition_tax_rate_pct": 1.0,
        "reverse_charge_applicable": False,
        "tax_compliance_rating": "MODERATE"
    })

    # 2. Regional Demand & Demographics
    demand_data = _load_json_data("district_demand_index.json")
    
    # Case-insensitive district lookup with fallback to 'default'
    district_info = None
    target_dist = str(district or "").strip().lower()
    
    for d_name, d_val in demand_data.items():
        if d_name.lower() == target_dist:
            district_info = d_val
            break
            
    if not district_info:
        district_info = demand_data.get("default", {
            "per_capita_spend_index": 1.0,
            "demand_elasticity": 0.85,
            "seasonal_variance_pct": 10.0,
            "credit_absorption_capacity": "MEDIUM",
            "high_demand_categories": []
        })

    # 3. Wholesale Margins & Procurement Benchmarks
    benchmark_data = _load_json_data("purchase_price_benchmarks.json")
    benchmarks = benchmark_data.get(cat_key, {
        "avg_gross_margin_pct": 20.0,
        "inventory_turnover_days": 20,
        "working_capital_share_pct": 50.0,
        "supplier_credit_days": 15
    })

    # 4. Derived Regional Demand Scoring
    base_demand = 60.0
    spend_mult = float(district_info.get("per_capita_spend_index", 1.0))
    high_dem_cats = [c.upper() for c in district_info.get("high_demand_categories", [])]
    
    if cat_key in high_dem_cats:
        base_demand += 20.0

    final_demand_score = min(round(base_demand * spend_mult, 1), 98.0)

    return {
        "category": cat_key,
        "tax_profile": taxes,
        "regional_demand": {
            "demand_score": final_demand_score,
            "per_capita_spend_index": spend_mult,
            "seasonal_variance_pct": district_info.get("seasonal_variance_pct", 10.0),
            "absorption_capacity": district_info.get("credit_absorption_capacity", "MEDIUM")
        },
        "purchase_benchmarks": benchmarks
    }