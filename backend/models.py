from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    preferred_language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'), ('hi', 'Hindi'), ('bn', 'Bengali'),
        ('mr', 'Marathi'), ('ta', 'Tamil'), ('te', 'Telugu'),
    ])
    state = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    block = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)


class BusinessCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    osm_tags = models.JSONField(default=list)  # e.g. ["shop=dairy", "shop=farm"]
    typical_margins_percent = models.FloatField(default=20.0)
    capex_ratio = models.FloatField(default=0.6)

    def __str__(self):
        return self.name


class LocalBusinessPOI(models.Model):
    """Cached ground-truth POIs — populated from Overpass API responses
    so repeat queries in the same area don't re-hit the public endpoint."""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(BusinessCategory, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    district = models.CharField(max_length=100, blank=True)
    block = models.CharField(max_length=100, blank=True)
    osm_id = models.BigIntegerField(null=True, blank=True)
    estimated_annual_turnover = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["latitude", "longitude"])]


class FeasibilityReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)

    proposed_category = models.ForeignKey(BusinessCategory, on_delete=models.PROTECT)
    village_name = models.CharField(max_length=150)
    block_name = models.CharField(max_length=150)
    district_name = models.CharField(max_length=150)
    center_lat = models.FloatField()
    center_lng = models.FloatField()
    margin_capital_available = models.DecimalField(max_digits=12, decimal_places=2)

    calculated_project_cost = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    selected_scheme_tier = models.CharField(max_length=50)
    interest_rate_pa = models.FloatField()
    tenure_years = models.IntegerField()
    moratorium_months = models.IntegerField()
    amortization_schedule = models.JSONField(default=list)

    competitor_count_5km = models.IntegerField(default=0)
    competitor_count_10km = models.IntegerField(default=0)
    estimated_market_saturation = models.CharField(max_length=50)

    market_reach_summary = models.TextField(blank=True)
    opportunity_analysis = models.JSONField(default=list)
    swot_strengths = models.JSONField(default=list)
    swot_weaknesses = models.JSONField(default=list)
    swot_opportunities = models.JSONField(default=list)
    swot_threats = models.JSONField(default=list)
    localized_risks = models.JSONField(default=list)
    suggested_pricing_strategy = models.JSONField(default=dict)
    dpr_ready_summary = models.TextField(blank=True)

    def __str__(self):
        return f"{self.village_name} · {self.proposed_category} · {self.created_at:%Y-%m-%d}"
