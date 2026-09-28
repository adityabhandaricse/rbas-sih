from rest_framework import serializers
from .models import User, BusinessCategory, LocalBusinessPOI, FeasibilityReport


class OTPLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    preferred_language = serializers.ChoiceField(
        choices=['en', 'hi', 'bn', 'mr', 'ta', 'te'], default='en'
    )


class CompetitorDensitySerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    category_code = serializers.CharField()
    radius_km = serializers.FloatField(default=10)


class StructureLoanSerializer(serializers.Serializer):
    margin_capital = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=5000)


class FeasibilityRequestSerializer(serializers.Serializer):
    village_name = serializers.CharField(max_length=150)
    block_name = serializers.CharField(max_length=150)
    district_name = serializers.CharField(max_length=150)
    center_lat = serializers.FloatField()
    center_lng = serializers.FloatField()
    margin_capital = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=5000)
    category_code = serializers.CharField()
    language = serializers.ChoiceField(choices=['en', 'hi', 'bn', 'mr', 'ta', 'te'], default='en')


class BusinessCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCategory
        fields = ["id", "name", "code", "osm_tags", "typical_margins_percent", "capex_ratio"]


class LocalBusinessPOISerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalBusinessPOI
        fields = ["id", "name", "category", "latitude", "longitude", "district", "block"]


class FeasibilityReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeasibilityReport
        fields = "__all__"
        read_only_fields = ["user", "created_at"]
