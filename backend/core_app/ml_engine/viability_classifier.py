import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve artifacts directory relative to this file:
# backend/core_app/ml_engine/artifacts/
CURRENT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = CURRENT_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "enterprise_viability.joblib"
SCALER_PATH = ARTIFACTS_DIR / "scaler.joblib"

_model = None
_scaler = None

FEATURE_COLUMNS = [
    "margin_capital",
    "total_project_cost",
    "monthly_emi",
    "competitor_count",
    "min_distance_km",
    "demand_score",
    "gross_margin",
    "gst_rate"
]


def _load_artifacts():
    """Loads serialized ML model and feature scaler into memory once."""
    global _model, _scaler
    if _model is None and MODEL_PATH.exists() and SCALER_PATH.exists():
        try:
            _model = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH)
            print(f"[ML Engine] Loaded production model from {ARTIFACTS_DIR}")
        except Exception as e:
            print(f"[ML Engine Error] Deserialization failure: {e}")
            logger.error(f"[ML Engine Error] Deserialization failure: {e}")
            _model, _scaler = None, None
    elif not MODEL_PATH.exists():
        print(f"[ML Engine Notice] Model artifact missing at {MODEL_PATH}. Using calibrated heuristic rules.")


def predict_viability(financial_data: dict, spatial_data: dict, market_data: dict) -> dict:
    """
    Infers the 0-100% Viability Score, default probability, credit risk tier,
    and quantitative contribution drivers.
    """
    _load_artifacts()

    # 1. Clean and normalize numerical parameters
    try:
        margin = float(financial_data.get("margin_capital") or 50000.0)
        total_cost = float(financial_data.get("total_project_cost") or (margin / 0.10))
        emi = float(financial_data.get("monthly_emi") or 0.0)
        
        comp_count = float(spatial_data.get("competitor_count") or 0.0)
        min_dist = float(spatial_data.get("min_distance_km") or 5.0)
        
        regional_dem = market_data.get("regional_demand") or {}
        demand_score = float(regional_dem.get("demand_score") or 70.0)
        
        benchmarks = market_data.get("purchase_benchmarks") or {}
        gross_margin = float(benchmarks.get("avg_gross_margin_pct") or 25.0)
        
        tax_profile = market_data.get("tax_profile") or {}
        gst_rate = float(tax_profile.get("gst_rate_pct") or 5.0)
    except (ValueError, TypeError) as parse_err:
        print(f"[ML Feature Warning] Value extraction issue: {parse_err}. Defaulting to safe values.")
        margin, total_cost, emi = 50000.0, 500000.0, 9124.0
        comp_count, min_dist = 0.0, 5.0
        demand_score, gross_margin, gst_rate = 70.0, 25.0, 5.0

    # 2. Build feature input matching training column definitions
    input_df = pd.DataFrame([[
        margin, total_cost, emi, comp_count, min_dist, demand_score, gross_margin, gst_rate
    ]], columns=FEATURE_COLUMNS)

    viability_score = None

    # 3. Model Inference with Heuristic Fallback
    if _model is not None and _scaler is not None:
        try:
            scaled_features = _scaler.transform(input_df.values)
            prob_success = _model.predict_proba(scaled_features)[0][1]
            viability_score = round(float(prob_success * 100.0), 1)
        except Exception as inf_err:
            print(f"[ML Inference Warning] Inference error: {inf_err}. Executing calibrated fallback.")
            viability_score = None

    if viability_score is None:
        viability_score = _calculate_heuristic_viability(
            margin=margin,
            total_cost=total_cost,
            emi=emi,
            comp_count=comp_count,
            min_dist=min_dist,
            demand_score=demand_score,
            gross_margin=gross_margin,
            gst_rate=gst_rate
        )

    # 4. Determine risk tiers and bank appraisal verdicts
    if viability_score >= 78.0:
        tier = "LOW RISK (PRIME)"
        verdict = "HIGHLY FEASIBLE: APPROVED UNDER PRIORITY LENDING NORMS"
    elif viability_score >= 55.0:
        tier = "MODERATE RISK"
        verdict = "FEASIBLE: CONDITIONAL ON WORKING CAPITAL MONITORING"
    else:
        tier = "HIGH RISK (DELINQUENCY HAZARD)"
        verdict = "UNFEASIBLE: HIGH COMPETITIVE SATURATION OR DEBT BURDEN"

    # 5. Extract Explainability Metrics for UI & Bank Officers
    equity_ratio = (margin / total_cost) if total_cost > 0 else 0.10
    spatial_pressure = comp_count / (min_dist + 0.5)

    return {
        "viability_score": viability_score,
        "default_probability_pct": round(max(0.0, min(100.0, 100.0 - viability_score)), 1),
        "risk_tier": tier,
        "appraisal_verdict": verdict,
        "key_drivers": {
            "equity_coverage_pct": round(equity_ratio * 100.0, 1),
            "competition_saturation_factor": round(spatial_pressure, 2),
            "effective_tax_rate_pct": gst_rate,
            "projected_gross_margin_pct": gross_margin
        }
    }


def _calculate_heuristic_viability(margin, total_cost, emi, comp_count, min_dist, demand_score, gross_margin, gst_rate):
    """
    Deterministic priority-sector credit viability calculation fallback.
    """
    score = 52.0

    # Equity Ratio Impact
    equity_ratio = (margin / total_cost) if total_cost > 0 else 0.10
    score += (equity_ratio - 0.10) * 85.0

    # Spatial Competition & Proximity
    if comp_count == 0:
        score += 12.0
    elif comp_count <= 2:
        score += 5.0
    elif comp_count > 5:
        score -= min(22.0, comp_count * 2.8)

    if min_dist > 2.5:
        score += 6.0
    elif min_dist < 0.5:
        score -= 8.5

    # Regional Demand Index Adjustment
    score += (demand_score - 50.0) * 0.25

    # Sector Margin Expansion & Tax Drag
    score += (gross_margin - 20.0) * 0.40
    score -= (gst_rate * 0.35)

    return max(15.0, min(95.0, round(score, 1)))