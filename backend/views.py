import os
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.template.loader import render_to_string

from .models import User, BusinessCategory, FeasibilityReport
from .serializers import (
    OTPLoginSerializer, CompetitorDensitySerializer, StructureLoanSerializer,
    FeasibilityRequestSerializer, FeasibilityReportSerializer,
)
from .calculators import structure_loan
from .geo_services import competitor_density_report
from .ai_services import generate_ai_feasibility_study


class OTPLoginView(APIView):
    """POST /api/v1/auth/otp-login/
    NOTE: OTP dispatch/verification (SMS gateway) is stubbed here — plug in
    MSG91 / Twilio Verify in production. This endpoint issues the JWT once
    the OTP step has been confirmed by the client."""
    permission_classes = [AllowAny]

    def post(self, request):
        ser = OTPLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone_number"]
        lang = ser.validated_data["preferred_language"]

        user, created = User.objects.get_or_create(
            phone_number=phone,
            defaults={"username": phone, "preferred_language": lang},
        )
        if not created:
            user.preferred_language = lang
            user.save(update_fields=["preferred_language"])

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_new_user": created,
        })


class CompetitorDensityView(APIView):
    """POST /api/v1/geo/competitors-density/"""
    permission_classes = [AllowAny]

    def post(self, request):
        ser = CompetitorDensitySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        category = BusinessCategory.objects.filter(code=d["category_code"]).first()
        if not category:
            return Response({"detail": "Unknown category_code"}, status=status.HTTP_404_NOT_FOUND)

        report = competitor_density_report(d["latitude"], d["longitude"], category.osm_tags)
        return Response(report)


class StructureLoanView(APIView):
    """POST /api/v1/finance/structure-loan/ — pure deterministic math."""
    permission_classes = [AllowAny]

    def post(self, request):
        ser = StructureLoanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        loan = structure_loan(ser.validated_data["margin_capital"])

        return Response({
            "margin_capital": str(loan.margin_capital),
            "total_project_cost": str(loan.total_project_cost),
            "loan_amount": str(loan.loan_amount),
            "scheme_name": loan.scheme_name,
            "scheme_tier": loan.scheme_tier,
            "interest_rate_pa": float(loan.interest_rate_pa),
            "tenure_years": loan.tenure_years,
            "moratorium_months": loan.moratorium_months,
            "amortization_schedule": [
                {"quarter": e.quarter, "phase": e.phase, "principal": str(e.principal),
                 "interest": str(e.interest), "total": str(e.total)}
                for e in loan.schedule
            ],
        })


class GenerateFeasibilityView(APIView):
    """POST /api/v1/advisory/generate-feasibility/
    Pipeline: financial calculator -> geospatial query -> Gemini structured
    advisory -> persist FeasibilityReport -> return full JSON."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = FeasibilityRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        category = BusinessCategory.objects.filter(code=d["category_code"]).first()
        if not category:
            return Response({"detail": "Unknown category_code"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Deterministic finance
        loan = structure_loan(d["margin_capital"])

        # 2. Geospatial competitor query
        geo_report = competitor_density_report(d["center_lat"], d["center_lng"], category.osm_tags)

        # 3. AI advisory (Gemini structured output)
        advisory = generate_ai_feasibility_study(
            financial_data={
                "margin_capital": str(loan.margin_capital),
                "total_project_cost": str(loan.total_project_cost),
                "loan_amount": str(loan.loan_amount),
                "scheme_name": loan.scheme_name,
                "interest_rate_pa": float(loan.interest_rate_pa),
                "tenure_years": loan.tenure_years,
                "moratorium_months": loan.moratorium_months,
            },
            geo_data={
                "village": d["village_name"], "block": d["block_name"], "district": d["district_name"],
                "competitor_count_10km": geo_report["competitor_count_10km"],
                "saturation_level": geo_report["saturation_10km"]["level"],
            },
            business_category=category.name,
            language=d["language"],
        )

        # 4. Persist
        report = FeasibilityReport.objects.create(
            user=request.user,
            proposed_category=category,
            village_name=d["village_name"], block_name=d["block_name"], district_name=d["district_name"],
            center_lat=d["center_lat"], center_lng=d["center_lng"],
            margin_capital_available=loan.margin_capital,
            calculated_project_cost=loan.total_project_cost,
            calculated_loan_amount=loan.loan_amount,
            selected_scheme_tier=loan.scheme_tier,
            interest_rate_pa=float(loan.interest_rate_pa),
            tenure_years=loan.tenure_years,
            moratorium_months=loan.moratorium_months,
            amortization_schedule=[
                {"quarter": e.quarter, "phase": e.phase, "principal": str(e.principal),
                 "interest": str(e.interest), "total": str(e.total)}
                for e in loan.schedule
            ],
            competitor_count_5km=geo_report["competitor_count_5km"],
            competitor_count_10km=geo_report["competitor_count_10km"],
            estimated_market_saturation=geo_report["saturation_10km"]["level"],
            market_reach_summary=advisory["market_reach_summary"],
            opportunity_analysis=advisory["opportunity_analysis"],
            swot_strengths=advisory["swot_strengths"],
            swot_weaknesses=advisory["swot_weaknesses"],
            swot_opportunities=advisory["swot_opportunities"],
            swot_threats=advisory["swot_threats"],
            localized_risks=advisory["localized_risks"],
            suggested_pricing_strategy=advisory["pricing_strategy"],
            dpr_ready_summary=advisory["bank_dpr_summary"],
        )

        return Response(FeasibilityReportSerializer(report).data, status=status.HTTP_201_CREATED)


class DownloadDPRPdfView(APIView):
    """GET /api/v1/reports/<id>/download-dpr-pdf/
    Renders the FeasibilityReport into a bank-ready DPR PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request, report_id):
        from django.http import HttpResponse
        from xhtml2pdf import pisa
        import io

        report = FeasibilityReport.objects.filter(id=report_id, user=request.user).first()
        if not report:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        html = render_to_string("dpr_template.html", {"report": report})
        buffer = io.BytesIO()
        pisa.CreatePDF(html, dest=buffer)
        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="DPR_{report.village_name}_{report.id}.pdf"'
        return response
