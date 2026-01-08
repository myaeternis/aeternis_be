"""
Serializers for the Pricing API.
"""

from rest_framework import serializers
from .models import (
    PlanType, StorageOption, PlaqueMaterial, 
    Addon, DiscountRule, PricingConfig
)


class StorageOptionSerializer(serializers.ModelSerializer):
    """Serializer for storage options."""
    display_storage = serializers.ReadOnlyField()
    
    class Meta:
        model = StorageOption
        fields = [
            'id',
            'storage_gb',
            'display_storage',
            'price',
            'estimated_photos',
            'estimated_video_minutes',
            'estimated_audio_hours',
        ]


class PlanTypeSerializer(serializers.ModelSerializer):
    """Serializer for plan types with nested storage options."""
    storage_options = StorageOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = PlanType
        fields = [
            'id',
            'slug',
            'name',
            'name_it',
            'name_en',
            'name_es',
            'description',
            'description_it',
            'description_en',
            'description_es',
            'has_video',
            'icon',
            'color_class',
            'gradient_class',
            'storage_options',
        ]


class PlaqueMaterialSerializer(serializers.ModelSerializer):
    """Serializer for plaque materials."""
    
    class Meta:
        model = PlaqueMaterial
        fields = [
            'id',
            'slug',
            'name',
            'name_it',
            'name_en',
            'name_es',
            'upgrade_price',
            'additional_price',
            'icon',
            'color_class',
            'bg_color_class',
            'is_included',
        ]


class AddonSerializer(serializers.ModelSerializer):
    """Serializer for add-ons."""
    
    class Meta:
        model = Addon
        fields = [
            'id',
            'slug',
            'addon_type',
            'name',
            'name_it',
            'name_en',
            'name_es',
            'description',
            'description_it',
            'description_en',
            'description_es',
            'price',
            'extension_years',
            'applies_to_profile',
            'applies_to_plaque',
            'icon',
        ]


class DiscountRuleSerializer(serializers.ModelSerializer):
    """Serializer for discount rules."""
    discount_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = DiscountRule
        fields = [
            'id',
            'slug',
            'discount_type',
            'name',
            'description',
            'min_items',
            'max_items',
            'discount_percentage',
            'discount_rate',
            'priority',
        ]


class PricingConfigSerializer(serializers.ModelSerializer):
    """Serializer for pricing configuration."""
    
    class Meta:
        model = PricingConfig
        fields = [
            'currency',
            'currency_symbol',
            'minimum_order_amount',
            'free_shipping_threshold',
            'shipping_cost',
            'tax_rate',
            'prices_include_tax',
        ]


class FullPricingSerializer(serializers.Serializer):
    """
    Complete pricing data for the frontend.
    Combines all pricing entities into a single response.
    """
    config = PricingConfigSerializer()
    plan_types = PlanTypeSerializer(many=True)
    materials = PlaqueMaterialSerializer(many=True)
    addons = AddonSerializer(many=True)
    discounts = DiscountRuleSerializer(many=True)
    
    # Structured data for easy frontend consumption
    plan_prices = serializers.SerializerMethodField()
    storage_options_by_plan = serializers.SerializerMethodField()
    plaque_upgrade_prices = serializers.SerializerMethodField()
    plaque_prices = serializers.SerializerMethodField()
    addon_prices = serializers.SerializerMethodField()
    discount_rates = serializers.SerializerMethodField()
    
    def get_plan_prices(self, obj):
        """
        Returns plan prices in format:
        { "myaeternis": { 0.25: 59, 0.5: 69, ... }, "story": { ... } }
        """
        result = {}
        for plan in obj['plan_types']:
            plan_prices = {}
            for storage in plan.storage_options.filter(is_active=True):
                # Use string keys for JSON compatibility
                key = float(storage.storage_gb)
                plan_prices[key] = float(storage.price)
            result[plan.slug] = plan_prices
        return result
    
    def get_storage_options_by_plan(self, obj):
        """
        Returns storage options per plan:
        { "myaeternis": [0.25, 0.5, 1, 2, 4], "story": [1, 2, 4, 8, 16] }
        """
        result = {}
        for plan in obj['plan_types']:
            options = list(
                plan.storage_options
                .filter(is_active=True)
                .order_by('sort_order', 'storage_gb')
                .values_list('storage_gb', flat=True)
            )
            result[plan.slug] = [float(o) for o in options]
        return result
    
    def get_plaque_upgrade_prices(self, obj):
        """
        Returns upgrade prices from included wood plaque:
        { "wood": 0, "plexiglass": 15, "brass": 35 }
        """
        return {
            m.slug: float(m.upgrade_price) 
            for m in obj['materials']
        }
    
    def get_plaque_prices(self, obj):
        """
        Returns prices for additional plaques:
        { "wood": 34, "plexiglass": 49, "brass": 79 }
        """
        return {
            m.slug: float(m.additional_price) 
            for m in obj['materials']
        }
    
    def get_addon_prices(self, obj):
        """
        Returns addon prices:
        { "extension": 49, "magnet": 10, "engraving": 19 }
        """
        return {
            a.slug: float(a.price) 
            for a in obj['addons']
        }
    
    def get_discount_rates(self, obj):
        """
        Returns discount rates as decimals:
        { "second_copy": 0.30, "third_plus_copy": 0.40, ... }
        """
        return {
            d.slug: float(d.discount_rate) 
            for d in obj['discounts']
        }

