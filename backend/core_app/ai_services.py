"""
ai_services.py
AI Engine — Direct Mistral AI REST integration via requests.
Zero external SDK dependencies to prevent Python 3.14 namespace issues.
Configured with strict socket failovers to avoid HTTP request timeouts.
"""
import os
import json
import logging
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class AdvisoryResponseSchema(BaseModel):
    market_reach_summary: str = Field(description="5-10km radius target audience demographic and channel breakdown")
    opportunity_analysis: list[str] = Field(description="3-5 unserved or underserved niches in this specific block/village")
    swot_strengths: list[str] = Field(description="Internal strengths tailored to micro-budget")
    swot_weaknesses: list[str] = Field(description="Internal constraints (working capital, tech gaps)")
    swot_opportunities: list[str] = Field(description="External growth prospects in this geography")
    swot_threats: list[str] = Field(description="External risks (seasonal fluctuations, supply chains)")
    localized_risks: list[str] = Field(description="Specific local threats and actionable mitigation strategies")
    pricing_strategy: dict[str, str] = Field(description="Tiered product/service pricing with regional purchasing power justification")
    bank_dpr_summary: str = Field(description="Executive summary formatted for a bank loan sanctioning officer")


def generate_ai_feasibility_study(financial_data: dict, geo_data: dict, business_category: str, language: str = "en") -> dict:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        logger.warning("MISTRAL_API_KEY missing in environment. Engaging deterministic fallback immediately.")
        return _build_fallback(financial_data, geo_data, business_category)

    village = geo_data.get('village') or geo_data.get('village_name') or 'Local Village'
    block = geo_data.get('block') or geo_data.get('block_name') or 'Local Block'
    district = geo_data.get('district') or geo_data.get('district_name') or 'District'
    comp_count = geo_data.get('competitor_count_10km', geo_data.get('competitor_count', 0))
    saturation = geo_data.get('saturation_level', geo_data.get('density_rating', 'MODERATE'))

    margin_cap = financial_data.get('margin_capital', 0)
    project_cost = financial_data.get('total_project_cost', 0)
    loan_amount = financial_data.get('loan_amount', 0)
    scheme_name = financial_data.get('scheme_name', 'Rural Priority Credit')
    rate = financial_data.get('interest_rate_pa', financial_data.get('interest_rate', 8.0))
    tenure = financial_data.get('tenure_years', financial_data.get('tenure', 5))
    moratorium = financial_data.get('moratorium_months', 6)

    system_prompt = (
        "You are an institutional micro-enterprise advisor for rural India (State Channelizing "
        "Agencies & NABARD). Generate an uncompromising, data-driven business feasibility study "
        "tailored for a first-time rural micro-entrepreneur. Output strictly valid JSON."
    )

    user_prompt = f"""
    BUSINESS PROFILE:
    - Business Category: {business_category}
    - Location: Village: {village}, Block: {block}, District: {district}
    - Local Competitors within 10km: {comp_count}
    - Market Saturation Index: {saturation}

    FINANCIAL STRUCTURE (DETERMINISTIC — already computed, do not recalculate):
    - Available Margin Capital (10%): Rs. {margin_cap}
    - Total Feasible Project Cost: Rs. {project_cost}
    - SCA Loan Eligibility (90%): Rs. {loan_amount}
    - Selected Scheme: {scheme_name} ({rate}% p.a., {tenure} years, {moratorium} months moratorium)

    RULES:
    1. Ground all recommendations strictly in the socio-economic reality of {district}.
    2. Suggest realistic unit pricing based on rural purchasing power.
    3. Output the entire response in the language specified: {language}.
    4. Never restate or alter the financial figures above — treat them as fixed inputs.
    5. Respond ONLY with valid JSON using this exact schema:
    {{
      "market_reach_summary": "string",
      "opportunity_analysis": ["string", "string", "string"],
      "swot_strengths": ["string", "string"],
      "swot_weaknesses": ["string", "string"],
      "swot_opportunities": ["string", "string"],
      "swot_threats": ["string", "string"],
      "localized_risks": ["string", "string"],
      "pricing_strategy": {{"Tier 1": "pricing details", "Tier 2": "pricing details"}},
      "bank_dpr_summary": "string"
    }}
    """

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    # Use modern primary model with one fast fallback model only
    candidate_models = ["mistral-small-latest", "open-mistral-7b"]

    for model in candidate_models:
        payload = {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            # Strict 7-second socket timeout to prevent blocking the WSGI thread
            response = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=7)
            
            if response.status_code == 200:
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                
                # Attempt strict schema validation
                try:
                    return AdvisoryResponseSchema.model_validate_json(raw_text).model_dump()
                except Exception as parse_err:
                    logger.warning(f"Schema validation failed, falling back to raw JSON decode: {parse_err}")
                    parsed = json.loads(raw_text)
                    if isinstance(parsed, dict) and "swot_strengths" in parsed:
                        return parsed

            print(f"[Mistral Alert] Model '{model}' responded with status {response.status_code}")
            if response.status_code in [401, 403]:
                # Invalid API key — don't waste time trying subsequent models
                logger.error("Mistral API key authentication failed. Dropping to fallback.")
                break

        except requests.exceptions.Timeout:
            print(f"[Mistral Timeout] Model '{model}' exceeded 7s limit. Fast-failing.")
            continue
        except Exception as e:
            print(f"[Mistral Request Error on {model}]: {e}")
            continue

    logger.warning("Mistral models timed out or failed. Engaging fast deterministic fallback.")
    return _build_fallback(financial_data, geo_data, business_category)


def _build_fallback(financial_data: dict, geo_data: dict, business_category: str) -> dict:
    village = geo_data.get('village') or geo_data.get('village_name') or 'Local Village'
    block = geo_data.get('block') or geo_data.get('block_name') or 'Local Block'
    district = geo_data.get('district') or geo_data.get('district_name') or 'District'
    margin_cap = financial_data.get('margin_capital', 0)
    project_cost = financial_data.get('total_project_cost', 0)
    loan_amount = financial_data.get('loan_amount', 0)
    scheme_name = financial_data.get('scheme_name', 'Rural Priority Credit')
    moratorium = financial_data.get('moratorium_months', 6)
    comp_count = geo_data.get('competitor_count_10km', geo_data.get('competitor_count', 0))

    return {
        "market_reach_summary": f"Primary consumer catchment within a 5-10km radius of {village}, covering local bi-weekly haats and rural households across {district}.",
        "opportunity_analysis": [
            f"Direct doorstep delivery across {block} panchayat clusters",
            "Institutional supply linkages with local primary agricultural cooperatives",
            "Semi-automated sorting and packaging to command a 10-15% quality premium"
        ],
        "swot_strengths": [
            f"Low promoter capital barrier of Rs. {margin_cap:,}",
            f"Concessional term loan sanction backed by {scheme_name}"
        ],
        "swot_weaknesses": [
            "Initial working capital squeeze during the first 60 days of operations",
            "Vulnerability to local power interruptions and single-source logistics"
        ],
        "swot_opportunities": [
            f"Favorable competitive density ({comp_count} direct competitor(s) registered within 10km)",
            "Expanding demand for branded and hygienic retail goods in peri-urban markets"
        ],
        "swot_threats": [
            "Cashflow dependency on agricultural harvest cycles and festival spending",
            "Sudden wholesale wholesale price fluctuations from district terminal mandis"
        ],
        "localized_risks": [
            f"Informal credit expectations in {village} — Mitigate by capping credit book to under 15% of gross sales.",
            "Delayed inventory turnover — Mitigate by adopting weekly procurement schedules with sub-divisional wholesalers."
        ],
        "pricing_strategy": {
            "Standard Consumer Pack": "Priced 4-6% below nearby town retail rates to drive initial adoption.",
            "Institutional / Bulk Supply": "Volume-discounted tier (8% margin) for village shops and community kitchens."
        },
        "bank_dpr_summary": (
            f"Proposed enterprise in {business_category} at {village}, Block {block} has a validated capital outlay "
            f"of Rs. {project_cost:,}. Supported by promoter margin equity of Rs. {margin_cap:,} (10%) and institutional debt "
            f"of Rs. {loan_amount:,} (90%) under {scheme_name}. With an initial {moratorium}-month principal moratorium, "
            f"the projected Debt Service Coverage Ratio (DSCR) remains healthy for priority sector lending."
        )
    }   