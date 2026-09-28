import logging
import requests
from dataclasses import is_dataclass, asdict
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Internal Module Imports
try:
    from .calculators import structure_loan as calc_structure_loan, saturation_index
except ImportError:
    calc_structure_loan = None
    saturation_index = None

from .ai_services import generate_ai_feasibility_study

# Core ML Engine Subsystem Import
try:
    from .ml_engine import run_ml_appraisal_pipeline
except ImportError:
    run_ml_appraisal_pipeline = None

logger = logging.getLogger(__name__)

# OSM Tag Mappings for Rural Competitor Queries
OSM_CATEGORY_TAGS = {
    "poultry": '["amenity"~"veterinary|marketplace"]["animal"~"poultry|chicken"]',
    "dairy": '["shop"~"dairy|farm"]["produce"~"milk"]',
    "grocery": '["shop"~"convenience|supermarket|general"]',
    "fertilizer": '["shop"~"agrarian|chemist|farm"]',
    "handicraft": '["shop"~"craft|artisan|gift"]',
    "tailor": '["shop"~"tailor|clothes|boutique"]',
    "bakery": '["shop"~"bakery|pastry"]',
    "salon": '["shop"~"hairdresser|beauty"]',
    "electronics": '["shop"~"electronics|mobile_phone"]',
    "hardware": '["shop"~"hardware|doityourself"]',
    "default": '["shop"]'
}


def serialize_structure(obj):
    """Safely converts dataclasses, Pydantic models, or objects into dicts."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return dict(obj)


def compute_deterministic_financials(margin_capital: float) -> dict:
    """
    Computes deterministic 90:10 SCA micro-credit financing, comprehensive
    yearly amortization schedule, and chart-ready dataset objects.
    """
    total_cost = round(margin_capital / 0.10, 2)
    loan_amount = round(total_cost * 0.90, 2)
    rate = 8.0
    tenure_years = 5
    moratorium_months = 6

    # Monthly interest rate & total payment periods
    r = (rate / 100.0) / 12.0
    n = tenure_years * 12

    if r > 0 and n > 0:
        emi = round((loan_amount * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1), 2)
    else:
        emi = round(loan_amount / n, 2)

    total_repayment = round(emi * n, 2)
    total_interest = round(total_repayment - loan_amount, 2)

    # 1. Compute Full Yearly Amortization Schedule
    schedule = []
    balance = loan_amount
    yearly_payment = emi * 12

    for yr in range(1, tenure_years + 1):
        interest_paid = round(balance * (rate / 100.0), 2)
        principal_paid = round(yearly_payment - interest_paid, 2)

        if principal_paid > balance or yr == tenure_years:
            principal_paid = balance
            closing_balance = 0.0
        else:
            closing_balance = round(balance - principal_paid, 2)

        schedule.append({
            "year": f"Year {yr}",
            "opening_balance": round(balance, 2),
            "principal": principal_paid,
            "interest": interest_paid,
            "closing_balance": closing_balance,
            "total_payment": round(principal_paid + interest_paid, 2)
        })
        balance = closing_balance

    # 2. Formulate Chart-Ready Datasets (Pie & Trajectory Bar/Line)
    chart_data = {
        "cost_breakdown": {
            "labels": ["Promoter Equity (10%)", "Institutional Debt (90%)"],
            "datasets": [
                {
                    "label": "Capital Outlay (₹)",
                    "data": [margin_capital, loan_amount],
                    "backgroundColor": ["#D4A62A", "#1F4D3C"],
                    "borderColor": ["#efe8d6", "#123028"],
                    "borderWidth": 1
                }
            ]
        },
        "repayment_trajectory": {
            "labels": [item["year"] for item in schedule],
            "datasets": [
                {
                    "label": "Principal Paid (₹)",
                    "data": [item["principal"] for item in schedule],
                    "backgroundColor": "#1F4D3C"
                },
                {
                    "label": "Interest Paid (₹)",
                    "data": [item["interest"] for item in schedule],
                    "backgroundColor": "#D4A62A"
                }
            ]
        }
    }

    # Verify if calculators.py has an override
    if calc_structure_loan:
        try:
            struct = calc_structure_loan(margin_capital)
            data = serialize_structure(struct)
            data.setdefault('margin_capital', margin_capital)
            data.setdefault('total_project_cost', total_cost)
            data.setdefault('loan_amount', loan_amount)
            data.setdefault('monthly_emi', emi)
            data.setdefault('total_interest', total_interest)
            data.setdefault('total_repayment', total_repayment)
            data.setdefault('amortization_schedule', schedule)
            data.setdefault('chart_data', chart_data)
            data.setdefault('scheme_name', 'Rural Priority Micro-Credit (SCA)')
            data.setdefault('interest_rate_pa', rate)
            data.setdefault('tenure_years', tenure_years)
            data.setdefault('moratorium_months', moratorium_months)
            return data
        except Exception as e:
            logger.warning(f"calc_structure_loan hook skipped: {e}")

    return {
        "margin_capital": margin_capital,
        "total_project_cost": total_cost,
        "loan_amount": loan_amount,
        "monthly_emi": emi,
        "total_interest": total_interest,
        "total_repayment": total_repayment,
        "amortization_schedule": schedule,
        "chart_data": chart_data,
        "interest_rate_pa": rate,
        "tenure_years": tenure_years,
        "moratorium_months": moratorium_months,
        "scheme_name": "Rural Priority Micro-Credit (SCA)",
    }


def get_saturation_label(comp_count: int) -> str:
    """Determines market saturation label safely."""
    if saturation_index:
        try:
            sat = saturation_index(comp_count)
            if isinstance(sat, dict):
                return sat.get("level", "MODERATE")
            if isinstance(sat, str):
                return sat
        except Exception:
            pass
            
    if comp_count == 0:
        return "LOW"
    elif comp_count <= 3:
        return "MODERATE"
    return "HIGH"


# --- 1. Finance: Deterministic Loan Structuring ---
@api_view(['POST', 'GET'])
def structure_loan(request):
    margin = request.data.get('margin_capital') if request.method == 'POST' else request.query_params.get('margin_capital')
    try:
        margin = float(margin or 50000)
    except (ValueError, TypeError):
        margin = 50000.0

    res_data = compute_deterministic_financials(margin)
    res_data["status"] = "success"
    return Response(res_data, status=status.HTTP_200_OK)


# --- 2. Auth: OTP / Citizen Login ---
@api_view(['POST'])
def otp_login(request):
    phone_or_user = request.data.get('phone') or request.data.get('username') or 'testuser'
    user, _ = User.objects.get_or_create(username=str(phone_or_user))
    refresh = RefreshToken.for_user(user)
    
    return Response({
        "status": "authenticated",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
        }
    }, status=status.HTTP_200_OK)


# --- 3. Geo: Competitor Density & Saturation ---
@api_view(['POST', 'GET'])
def competitors_density(request):
    params = request.data if request.method == 'POST' else request.query_params
    
    try:
        lat = float(params.get('latitude') or params.get('center_lat') or 23.0673)
        lng = float(params.get('longitude') or params.get('center_lng') or 87.3163)
        radius_km = float(params.get('radius_km', 10.0))
    except (ValueError, TypeError):
        lat, lng, radius_km = 23.0673, 87.3163, 10.0

    category_key = str(params.get('business_type') or params.get('category') or 'grocery').lower()
    radius_meters = int(radius_km * 1000)
    tag = OSM_CATEGORY_TAGS.get(category_key, OSM_CATEGORY_TAGS["default"])
    
    query = f"""
    [out:json][timeout:15];
    (
      node{tag}(around:{radius_meters},{lat},{lng});
      way{tag}(around:{radius_meters},{lat},{lng});
    );
    out center;
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    competitors = []
    try:
        res = requests.post(
            overpass_url, 
            data={'data': query}, 
            headers={'User-Agent': 'GramSetu-GeoService/1.0'}, 
            timeout=10
        )
        if res.status_code == 200:
            elements = res.json().get('elements', [])
            for item in elements:
                item_lat = item.get('lat') or item.get('center', {}).get('lat')
                item_lon = item.get('lon') or item.get('center', {}).get('lon')
                if item_lat and item_lon:
                    name = item.get('tags', {}).get('name', f"Nearby {category_key.capitalize()} Outlet")
                    competitors.append({
                        "id": item['id'],
                        "osm_id": item['id'],
                        "name": name,
                        "lat": item_lat,
                        "lon": item_lon,
                        "lng": item_lon,
                        "category": category_key
                    })
    except Exception as e:
        logger.warning(f"Overpass query failed: {e}. Returning empty competitor pool.")

    saturation_level = get_saturation_label(len(competitors))

    return Response({
        "status": "success",
        "category": category_key,
        "center": {"lat": lat, "lng": lng, "lon": lng},
        "radius_km": radius_km,
        "competitor_count": len(competitors),
        "saturation_level": saturation_level,
        "competitors": competitors
    }, status=status.HTTP_200_OK)


# --- 4. Advisory: AI Business Feasibility + ML Engine ---
@api_view(['POST'])
def generate_feasibility(request):
    """
    Generates structured AI advisory and executes the ML Engine (Market Intelligence,
    Spatial Density, Viability Scoring, and Strategic Decision Matrix).
    """
    body = request.data or {}
    
    # 1. Clean margin capital & compute deterministic financials
    try:
        margin = float(body.get('margin_capital', body.get('margin', 50000)))
    except (ValueError, TypeError):
        margin = 50000.0

    fin_structure = compute_deterministic_financials(margin)
    
    # 2. Clean competitor density & saturation
    try:
        comp_count = int(body.get('competitor_count') or body.get('competitor_count_10km') or 0)
    except (ValueError, TypeError):
        comp_count = 0

    sat_level = body.get('saturation_level') or get_saturation_label(comp_count)
    competitors_list = body.get('competitors', [])

    # 3. Clean geography coordinates
    try:
        lat = float(body.get('latitude') or body.get('center_lat') or 23.0708)
        lng = float(body.get('longitude') or body.get('center_lng') or 87.3167)
    except (ValueError, TypeError):
        lat, lng = 23.0708, 87.3167

    village = body.get('village') or body.get('village_name') or 'Local Area'
    block = body.get('block') or body.get('block_name') or 'Local Block'
    district = body.get('district') or body.get('district_name') or 'Local District'
    state = body.get('state', '')

    geo_data = {
        "village": village,
        "block": block,
        "district": district,
        "state": state,
        "latitude": lat,
        "longitude": lng,
        "competitor_count_10km": comp_count,
        "competitor_count": comp_count,
        "saturation_level": sat_level
    }
    
    business_category = (
        body.get('business_category') 
        or body.get('category_code') 
        or body.get('category') 
        or 'Grocery / General store'
    )
    language = body.get('language', 'en')

    try:
        # A. Qualitative Feasibility Study
        report = generate_ai_feasibility_study(
            financial_data=fin_structure,
            geo_data=geo_data,
            business_category=business_category,
            language=language
        )

        # B. Execute Machine Learning Appraisal Pipeline
        ml_output = None
        if run_ml_appraisal_pipeline:
            try:
                ml_output = run_ml_appraisal_pipeline(
                    financial_data=fin_structure,
                    geo_data=geo_data,
                    category=business_category,
                    competitors=competitors_list
                )
            except Exception as ml_err:
                logger.error(f"ML Pipeline execution failed: {ml_err}", exc_info=True)

        # C. Extract Dynamic ML Predictions
        viability_pred = (ml_output or {}).get("viability_prediction", {})
        dynamic_score = viability_pred.get("viability_score", 72.5)
        dynamic_tier = viability_pred.get("risk_tier", "MODERATE RISK")

        # D. Merge Statistical, Financial, and ML Data directly into Report
        if isinstance(report, dict):
            report.update({
                "margin_capital": fin_structure["margin_capital"],
                "total_project_cost": fin_structure["total_project_cost"],
                "loan_amount": fin_structure["loan_amount"],
                "monthly_emi": fin_structure["monthly_emi"],
                "total_interest": fin_structure["total_interest"],
                "total_repayment": fin_structure["total_repayment"],
                "amortization_schedule": fin_structure["amortization_schedule"],
                "chart_data": fin_structure["chart_data"],
                "interest_rate_pa": fin_structure["interest_rate_pa"],
                "tenure_years": fin_structure["tenure_years"],
                "moratorium_months": fin_structure["moratorium_months"],
                "scheme_name": fin_structure["scheme_name"],
                "competitor_count": comp_count,
                "competitor_count_10km": comp_count,
                "saturation_level": sat_level,
                "village": village,
                "block": block,
                "district": district,
                "state": state,
                "latitude": lat,
                "longitude": lng,
                "business_category": business_category,
                "ml_appraisal": ml_output,
                "viability_score": dynamic_score,
                "risk_tier": dynamic_tier
            })

        return Response({
            "status": "success",
            "report": report,
            "finance": fin_structure,
            "geography": geo_data,
            "ml_appraisal": ml_output,
            "viability_score": dynamic_score,
            "risk_tier": dynamic_tier
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("Advisory generation failed:")
        print(f"\n[Generate Feasibility Error]: {e}\n")
        return Response({
            "status": "error",
            "message": f"Feasibility generation failed: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 5. Integrated Pipeline: Full Evaluation ---
@api_view(['POST'])
def full_feasibility_evaluation(request):
    """
    Autonomous batch evaluation: fetches competitors, calculates finances,
    runs the ML appraisal, and triggers the AI report in a single roundtrip.
    """
    data = request.data or {}
    try:
        margin = float(data.get('margin_capital', 50000))
        lat = float(data.get('latitude') or data.get('center_lat') or 23.0673)
        lng = float(data.get('longitude') or data.get('center_lng') or 87.3163)
    except (ValueError, TypeError):
        margin, lat, lng = 50000.0, 23.0673, 87.3163

    category = str(data.get('category') or data.get('business_type') or 'grocery').lower()
    village = data.get('village') or data.get('village_name') or 'Bishnupur'
    block = data.get('block') or data.get('block_name') or 'Bishnupur'
    district = data.get('district') or data.get('district_name') or 'Bankura'
    state = data.get('state', '')
    language = data.get('language', 'en')

    # 1. Deterministic Financials & Amortization
    fin_data = compute_deterministic_financials(margin)

    # 2. OSM Live Competitors
    radius_km = 10.0
    radius_meters = int(radius_km * 1000)
    tag = OSM_CATEGORY_TAGS.get(category, OSM_CATEGORY_TAGS["default"])
    query = f"""
    [out:json][timeout:15];
    (
      node{tag}(around:{radius_meters},{lat},{lng});
      way{tag}(around:{radius_meters},{lat},{lng});
    );
    out center;
    """
    competitors = []
    try:
        res = requests.post(
            "https://overpass-api.de/api/interpreter", 
            data={'data': query}, 
            headers={'User-Agent': 'GramSetu-Pipeline/1.0'}, 
            timeout=10
        )
        if res.status_code == 200:
            for item in res.json().get('elements', []):
                item_lat = item.get('lat') or item.get('center', {}).get('lat')
                item_lon = item.get('lon') or item.get('center', {}).get('lon')
                if item_lat and item_lon:
                    competitors.append({
                        "id": item['id'],
                        "osm_id": item['id'],
                        "name": item.get('tags', {}).get('name', f"Nearby {category.capitalize()} Entity"),
                        "lat": item_lat,
                        "lon": item_lon,
                        "lng": item_lon,
                        "category": category
                    })
    except Exception as e:
        logger.warning(f"Overpass pipeline query failed: {e}")

    comp_count = len(competitors)
    saturation_level = get_saturation_label(comp_count)

    # 3. Geography Payload
    geo_data = {
        "village": village,
        "block": block,
        "district": district,
        "state": state,
        "latitude": lat,
        "longitude": lng,
        "competitor_count_10km": comp_count,
        "competitor_count": comp_count,
        "saturation_level": saturation_level
    }
    
    # 4. AI Advisory
    ai_report = generate_ai_feasibility_study(
        financial_data=fin_data,
        geo_data=geo_data,
        business_category=category,
        language=language
    )

    # 5. Machine Learning Appraisal Engine
    ml_output = None
    if run_ml_appraisal_pipeline:
        try:
            ml_output = run_ml_appraisal_pipeline(
                financial_data=fin_data,
                geo_data=geo_data,
                category=category,
                competitors=competitors
            )
        except Exception as ml_err:
            logger.error(f"ML Pipeline execution warning in full evaluation: {ml_err}", exc_info=True)

    # 6. Extract Dynamic Predictions
    viability_pred = (ml_output or {}).get("viability_prediction", {})
    dynamic_score = viability_pred.get("viability_score", 72.5)
    dynamic_tier = viability_pred.get("risk_tier", "MODERATE RISK")

    # 7. Unify Outputs
    if isinstance(ai_report, dict):
        ai_report.update({
            "margin_capital": fin_data["margin_capital"],
            "total_project_cost": fin_data["total_project_cost"],
            "loan_amount": fin_data["loan_amount"],
            "monthly_emi": fin_data["monthly_emi"],
            "total_interest": fin_data["total_interest"],
            "total_repayment": fin_data["total_repayment"],
            "amortization_schedule": fin_data["amortization_schedule"],
            "chart_data": fin_data["chart_data"],
            "interest_rate_pa": fin_data["interest_rate_pa"],
            "tenure_years": fin_data["tenure_years"],
            "moratorium_months": fin_data["moratorium_months"],
            "scheme_name": fin_data["scheme_name"],
            "competitor_count": comp_count,
            "competitor_count_10km": comp_count,
            "saturation_level": saturation_level,
            "village": village,
            "block": block,
            "district": district,
            "state": state,
            "latitude": lat,
            "longitude": lng,
            "business_category": category,
            "ml_appraisal": ml_output,
            "viability_score": dynamic_score,
            "risk_tier": dynamic_tier
        })

    return Response({
        "status": "success",
        "financials": fin_data,
        "geography": {
            "center": {"lat": lat, "lng": lng, "lon": lng},
            "radius_km": radius_km,
            "competitor_count": comp_count,
            "saturation_level": saturation_level,
            "competitors": competitors
        },
        "report": ai_report,
        "advisory": ai_report,
        "ml_appraisal": ml_output,
        "viability_score": dynamic_score,
        "risk_tier": dynamic_tier
    }, status=status.HTTP_200_OK)


# --- 6. Catch-All Stub for Any Missing URL Patterns ---
def __getattr__(name):
    @api_view(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    def placeholder_view(request, *args, **kwargs):
        return Response({
            "status": "pending_implementation",
            "endpoint": name,
            "message": f"Endpoint '{name}' is currently being developed."
        })
    return placeholder_view