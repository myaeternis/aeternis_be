"""
API Views for Pricing.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import (
    PlanType, PlaqueMaterial, Addon, 
    DiscountRule, PricingConfig
)
from .serializers import (
    PlanTypeSerializer, PlaqueMaterialSerializer,
    AddonSerializer, DiscountRuleSerializer,
    PricingConfigSerializer, FullPricingSerializer
)


class PricingView(APIView):
    """
    GET /api/pricing/
    
    Returns all pricing data needed by the frontend in a single request.
    This endpoint is designed to replace the static pricing.js file.
    """
    
    def get(self, request):
        # Fetch all active pricing data
        config = PricingConfig.get_config()
        plan_types = PlanType.objects.filter(is_active=True).prefetch_related(
            'storage_options'
        )
        materials = PlaqueMaterial.objects.filter(is_active=True)
        addons = Addon.objects.filter(is_active=True)
        discounts = DiscountRule.objects.filter(is_active=True)
        
        # Prepare data for serializer
        data = {
            'config': config,
            'plan_types': plan_types,
            'materials': materials,
            'addons': addons,
            'discounts': discounts,
        }
        
        serializer = FullPricingSerializer(data)
        return Response(serializer.data)


class PlanTypesView(APIView):
    """
    GET /api/pricing/plans/
    
    Returns only plan types with their storage options.
    """
    
    def get(self, request):
        plans = PlanType.objects.filter(is_active=True).prefetch_related(
            'storage_options'
        )
        serializer = PlanTypeSerializer(plans, many=True)
        return Response(serializer.data)


class MaterialsView(APIView):
    """
    GET /api/pricing/materials/
    
    Returns available plaque materials.
    """
    
    def get(self, request):
        materials = PlaqueMaterial.objects.filter(is_active=True)
        serializer = PlaqueMaterialSerializer(materials, many=True)
        return Response(serializer.data)


class AddonsView(APIView):
    """
    GET /api/pricing/addons/
    
    Returns available add-ons.
    """
    
    def get(self, request):
        addons = Addon.objects.filter(is_active=True)
        serializer = AddonSerializer(addons, many=True)
        return Response(serializer.data)


class DiscountsView(APIView):
    """
    GET /api/pricing/discounts/
    
    Returns discount rules.
    """
    
    def get(self, request):
        discounts = DiscountRule.objects.filter(is_active=True)
        serializer = DiscountRuleSerializer(discounts, many=True)
        return Response(serializer.data)
