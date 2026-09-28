def generate_strategic_decisions(viability: dict, market: dict, spatial: dict) -> dict:
    """
    Generates prescriptive recommendations across tax planning, inventory, and location strategy.
    """
    actions = []
    warnings = []
    growth_levers = []

    tax_profile = market.get("tax_profile", {})
    benchmarks = market.get("purchase_benchmarks", {})
    demand = market.get("regional_demand", {})
    comp_count = spatial.get("competitor_count", 0)
    min_dist = spatial.get("min_distance_km", 5.0)
    viability_score = viability.get("viability_score", 50.0)

    # 1. Tax & Regulatory Strategy
    if tax_profile.get("composition_scheme_eligible") and tax_profile.get("gst_rate_pct", 0) > 0:
        comp_rate = tax_profile.get("composition_tax_rate_pct", 1.0)
        actions.append({
            "pillar": "Tax Optimization",
            "title": "Register Under GST Composition Scheme",
            "detail": f"Standard GST is {tax_profile.get('gst_rate_pct')}%. Enrolling in Composition reduces liability to flat {comp_rate}%, eliminating complex input tax credit reconciliations."
        })
    elif tax_profile.get("gst_rate_pct") == 0.0:
        actions.append({
            "pillar": "Tax Optimization",
            "title": "Zero-Tax Agricultural Exemption",
            "detail": "Category is exempt from GST. Maintain local mandi/cooperative purchase receipts to easily access priority sector subvention benefits."
        })

    # 2. Inventory & Working Capital
    wc_share = benchmarks.get("working_capital_share_pct", 50.0)
    credit_days = benchmarks.get("supplier_credit_days", 15)
    actions.append({
        "pillar": "Procurement & Cash Flow",
        "title": f"Strict {credit_days}-Day Working Capital Cycle",
        "detail": f"{wc_share}% of capital outlay will be locked in operational stock. Secure minimum {credit_days} days credit terms with wholesale distributors to protect cash flow."
    })

    # 3. Spatial Competition & Saturation
    if comp_count >= 5 and min_dist < 1.0:
        warnings.append({
            "title": "High Cluster Proximity Alert",
            "detail": f"{comp_count} direct competitors identified with the nearest only {min_dist}km away. Avoid price undercutting; focus on product bundling and home delivery to peripheral hamlets."
        })
    elif comp_count == 0:
        growth_levers.append({
            "title": "First-Mover Catchment Monopoly",
            "detail": "Zero competitors detected within radial boundary. Secure exclusive distributorships to establish high local switching costs."
        })

    # 4. Regional Demand Strategy
    if demand.get("seasonal_variance_pct", 0) > 12.0:
        warnings.append({
            "title": "High Demand Seasonality",
            "detail": f"Subject to {demand.get('seasonal_variance_pct')}% seasonal volatility. Build 2 months of debt repayment reserve during harvest/peak festival cash influx."
        })

    growth_levers.append({
        "title": "Value Addition & Margin Expansion",
        "detail": f"Local sector average gross margin is {benchmarks.get('avg_gross_margin_pct')}%. Introducing packaged or semi-processed stock can expand net margins by 4-7%."
    })

    return {
        "immediate_actions": actions,
        "risk_warnings": warnings,
        "growth_levers": growth_levers
    }