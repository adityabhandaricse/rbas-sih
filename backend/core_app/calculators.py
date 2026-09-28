"""
calculators.py
Deterministic financial & spatial engine — Section 3 of the system spec.
NO LLM involvement anywhere in this file. Pure arithmetic only.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from dataclasses import dataclass, field, asdict
from math import radians, sin, cos, asin, sqrt, pi


MARGIN_FRACTION = Decimal("0.10")
LOAN_FRACTION = Decimal("0.90")

TIER_MICRO = "MICRO_FINANCE"
TIER_TERM = "TERM_LOAN"


@dataclass
class QuarterEntry:
    quarter: int
    phase: str  # "MORATORIUM" | "AMORTIZATION"
    principal: Decimal
    interest: Decimal
    total: Decimal

    def to_dict(self) -> dict:
        return {
            "quarter": self.quarter,
            "phase": self.phase,
            "principal": float(self.principal),
            "interest": float(self.interest),
            "total": float(self.total)
        }


@dataclass
class LoanStructure:
    margin_capital: Decimal
    total_project_cost: Decimal
    loan_amount: Decimal
    scheme_tier: str
    scheme_name: str
    interest_rate_pa: Decimal
    tenure_years: int
    moratorium_months: int
    schedule: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converts the structure to a JSON-serializable dictionary with frontend compatibility keys."""
        # Derive representative monthly values for the UI summary cards
        amortization_entries = [e for e in self.schedule if e.phase == "AMORTIZATION"]
        avg_monthly_installment = (
            float(amortization_entries[0].total / Decimal("3")) if amortization_entries else 0.0
        )

        return {
            # Canonical Spec Fields
            "margin_capital": float(self.margin_capital),
            "total_project_cost": float(self.total_project_cost),
            "loan_amount": float(self.loan_amount),
            "scheme_tier": self.scheme_tier,
            "scheme_name": self.scheme_name,
            "interest_rate_pa": float(self.interest_rate_pa),
            "tenure_years": self.tenure_years,
            "moratorium_months": self.moratorium_months,
            "schedule": [e.to_dict() for e in self.schedule],

            # Frontend Aliases & UI Compatibility (prevents NaN / undefined)
            "eligible_loan_amount": float(self.loan_amount),
            "project_cost": float(self.total_project_cost),
            "interest_rate": float(self.interest_rate_pa),
            "annual_interest_rate": f"{self.interest_rate_pa}%",
            "tenure": self.tenure_years,
            "tenure_months": self.tenure_years * 12,
            "monthly_emi": round(avg_monthly_installment, 2),
            "estimated_monthly_emi": round(avg_monthly_installment, 2),
            "subsidy_eligible": self.scheme_tier in [TIER_MICRO, TIER_TERM]
        }


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def structure_loan(margin_capital) -> LoanStructure:
    """
    Implements the deterministic scheme-routing decision tree exactly as
    specified in Section 3 of the system design.
    """
    try:
        margin_capital = Decimal(str(margin_capital).strip())
        if margin_capital <= Decimal("0"):
            margin_capital = Decimal("10000.00")
    except (InvalidOperation, TypeError, ValueError):
        margin_capital = Decimal("10000.00")

    total_project_cost = margin_capital / MARGIN_FRACTION
    raw_loan = total_project_cost * LOAN_FRACTION

    if total_project_cost <= Decimal("140000"):
        tier = TIER_MICRO
        scheme_name = "Micro Finance Scheme"
        ceiling = Decimal("125000")
        rate = Decimal("6.5")
        tenure_years = 3
        total_quarters = 12
        moratorium_quarters = 1
    elif total_project_cost <= Decimal("5000000"):
        tier = TIER_TERM
        scheme_name = "Term Loan Scheme"
        ceiling = Decimal("4500000")
        rate = Decimal("8.0")
        tenure_years = 7
        total_quarters = 28
        moratorium_quarters = 2
    else:
        # Outside standard State Channelizing Agency ceiling.
        tier = "OUT_OF_RANGE"
        scheme_name = "Exceeds standard SCA ceiling — route to project finance"
        ceiling = raw_loan
        rate = Decimal("8.0")
        tenure_years = 7
        total_quarters = 28
        moratorium_quarters = 2

    loan_amount = min(raw_loan, ceiling)
    active_quarters = total_quarters - moratorium_quarters
    quarterly_rate = rate / (Decimal("4") * Decimal("100"))
    principal_per_quarter = loan_amount / Decimal(active_quarters)

    schedule = []
    for q in range(1, moratorium_quarters + 1):
        interest = loan_amount * quarterly_rate
        schedule.append(QuarterEntry(
            quarter=q,
            phase="MORATORIUM",
            principal=Decimal("0.00"),
            interest=_round(interest),
            total=_round(interest)
        ))

    for k in range(1, active_quarters + 1):
        principal_remaining = loan_amount - (Decimal(k - 1) * principal_per_quarter)
        interest = principal_remaining * quarterly_rate
        total = principal_per_quarter + interest
        schedule.append(QuarterEntry(
            quarter=moratorium_quarters + k,
            phase="AMORTIZATION",
            principal=_round(principal_per_quarter),
            interest=_round(interest),
            total=_round(total)
        ))

    return LoanStructure(
        margin_capital=_round(margin_capital),
        total_project_cost=_round(total_project_cost),
        loan_amount=_round(loan_amount),
        scheme_tier=tier,
        scheme_name=scheme_name,
        interest_rate_pa=rate,
        tenure_years=tenure_years,
        moratorium_months=moratorium_quarters * 3,
        schedule=schedule,
    )


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0
    dlat = radians(float(lat2) - float(lat1))
    dlon = radians(float(lon2) - float(lon1))
    a = sin(dlat / 2) ** 2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def saturation_index(count: int, radius_km: float) -> dict:
    """Calculates spatial competitor density and market saturation tier."""
    radius = float(radius_km) if radius_km > 0 else 5.0
    area = pi * (radius ** 2)
    density = count / area

    if count == 0:
        level = "LOW"
    elif count <= 2:
        level = "MODERATE"
    elif count <= 5:
        level = "HIGH"
    else:
        level = "OVERSATURATED"

    return {
        "competitor_count": count,
        "radius_km": radius,
        "area_sq_km": round(area, 2),
        "density_per_sq_km": round(density, 5),
        "level": level
    }