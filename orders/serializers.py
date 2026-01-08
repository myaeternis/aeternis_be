"""
Serializers for Orders API.
"""

from rest_framework import serializers
from decimal import Decimal

from .models import Order, OrderProfile, OrderPlaque
from pricing.models import (
    PlanType, StorageOption, PlaqueMaterial, 
    Addon, DiscountRule, PricingConfig
)


class PlaqueInputSerializer(serializers.Serializer):
    """Serializer for plaque input from frontend."""
    id = serializers.CharField(required=False)
    material = serializers.SlugField()
    magnet = serializers.BooleanField(default=False)
    engraving = serializers.BooleanField(default=False)


class ProfileInputSerializer(serializers.Serializer):
    """Serializer for profile input from frontend."""
    id = serializers.CharField(required=False)
    name = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')
    planType = serializers.SlugField()
    storage = serializers.DecimalField(max_digits=6, decimal_places=2)
    extensionYears = serializers.IntegerField(min_value=0, default=0, required=False)
    plaques = PlaqueInputSerializer(many=True)


class OrderInputSerializer(serializers.Serializer):
    """
    Serializer for order creation from frontend.
    Validates the cart data and customer info.
    """
    # Customer info
    email = serializers.EmailField()
    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    # Shipping address
    addressLine1 = serializers.CharField(max_length=255)
    addressLine2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postalCode = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2, default='IT')
    
    # Cart data
    profiles = ProfileInputSerializer(many=True)
    language = serializers.CharField(max_length=5, default='it')
    
    def validate_profiles(self, value):
        """Ensure at least one profile with at least one plaque."""
        if not value:
            raise serializers.ValidationError("At least one profile is required.")
        
        for profile in value:
            if not profile.get('plaques'):
                raise serializers.ValidationError(
                    f"Profile '{profile.get('name', 'Unknown')}' must have at least one plaque."
                )
        
        return value


class OrderPlaqueSerializer(serializers.ModelSerializer):
    """Serializer for order plaque output."""
    
    class Meta:
        model = OrderPlaque
        fields = [
            'id',
            'material_slug',
            'is_included',
            'base_price',
            'upgrade_price',
            'discount_rate',
            'discount_amount',
            'has_magnet',
            'magnet_price',
            'has_engraving',
            'engraving_price',
            'final_price',
        ]


class OrderProfileSerializer(serializers.ModelSerializer):
    """Serializer for order profile output."""
    plaques = OrderPlaqueSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderProfile
        fields = [
            'id',
            'name',
            'plan_type_slug',
            'storage_gb',
            'plan_price',
            'extension_years',
            'extension_price',
            'profile_subtotal',
            'plaques',
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for order output."""
    profiles = OrderProfileSerializer(many=True, read_only=True)
    customer_full_name = serializers.ReadOnlyField()
    profile_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'customer_email',
            'customer_full_name',
            'customer_phone',
            'shipping_address_line1',
            'shipping_address_line2',
            'shipping_city',
            'shipping_state',
            'shipping_postal_code',
            'shipping_country',
            'subtotal',
            'plans_cost',
            'plaques_cost',
            'addons_cost',
            'copy_discount',
            'bundle_discount',
            'bundle_discount_rate',
            'shipping_cost',
            'total',
            'currency',
            'profile_count',
            'language',
            'created_at',
            'paid_at',
            'profiles',
        ]


class OrderSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for order lists."""
    customer_full_name = serializers.ReadOnlyField()
    profile_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'customer_email',
            'customer_full_name',
            'total',
            'currency',
            'profile_count',
            'created_at',
        ]


class CalculateTotalInputSerializer(serializers.Serializer):
    """
    Serializer for price calculation requests.
    Used to validate cart totals on the backend.
    """
    profiles = ProfileInputSerializer(many=True)
    
    def validate_profiles(self, value):
        if not value:
            raise serializers.ValidationError("At least one profile is required.")
        return value

