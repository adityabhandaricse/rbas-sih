from .market_intelligence import analyze_market_conditions
from .competitor_spatial import extract_spatial_density_features
from .viability_classifier import predict_viability
from .decision_matrix import generate_strategic_decisions


def run_ml_appraisal_pipeline(
    financial_data: dict, 
    geo_data: dict, 
    category: str, 
    competitors: list = None
) -> dict:
    """
    Executes the end-to-end ML intelligence & decision pipeline.
    """
    competitors = competitors or []
    district = geo_data.get("district") or geo_data.get("district_name") or "default"

    try:
        lat = float(geo_data.get("latitude", 23.0))
        lng = float(geo_data.get("longitude", 87.0))
    except (ValueError, TypeError):
        lat, lng = 23.0, 87.0

    # 1. Market & Tax Intelligence (GST, MOSPI demand, margin benchmarks)
    market_intel = analyze_market_conditions(category=category, district=district)

    # 2. Spatial Density Analysis (Nearest competitor distance, clustering)
    spatial_intel = extract_spatial_density_features(
        center_lat=lat, 
        center_lng=lng, 
        competitors=competitors
    )

    # 3. Viability Inference (Random Forest classifier prediction)
    viability = predict_viability(
        financial_data=financial_data, 
        spatial_data=spatial_intel, 
        market_data=market_intel
    )

    # 4. Prescriptive Decisions & Strategic Roadmap
    decisions = generate_strategic_decisions(
        viability=viability, 
        market=market_intel, 
        spatial=spatial_intel
    )

    return {
        "market_intelligence": market_intel,
        "spatial_intelligence": spatial_intel,
        "viability_prediction": viability,
        "strategic_decisions": decisions,
        # Alias provided for UI compatibility across all advisory cards
        "strategic_recommendations": decisions
    }