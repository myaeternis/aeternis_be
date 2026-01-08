"""
Order calculation and creation services.

This module contains the business logic for calculating order totals
and creating orders from cart data.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional

from django.db import transaction

from pricing.models import (
    PlanType, StorageOption, PlaqueMaterial, 
    Addon, DiscountRule, PricingConfig
)
from .models import Order, OrderProfile, OrderPlaque, OrderStatusHistory


class PricingService:
    """
    Service for calculating prices.
    Mirrors the frontend pricing logic for validation.
    """
    
    def __init__(self):
        self.config = PricingConfig.get_config()
        self._cache = {}
    
    def _get_plan_type(self, slug: str) -> Optional[PlanType]:
        """Get plan type by slug with caching."""
        if slug not in self._cache.get('plans', {}):
            if 'plans' not in self._cache:
                self._cache['plans'] = {}
            try:
                self._cache['plans'][slug] = PlanType.objects.get(slug=slug, is_active=True)
            except PlanType.DoesNotExist:
                return None
        return self._cache['plans'].get(slug)
    
    def _get_storage_option(self, plan_slug: str, storage_gb: Decimal) -> Optional[StorageOption]:
        """Get storage option by plan and storage amount."""
        key = f"{plan_slug}_{storage_gb}"
        if key not in self._cache.get('storage', {}):
            if 'storage' not in self._cache:
                self._cache['storage'] = {}
            try:
                plan = self._get_plan_type(plan_slug)
                if plan:
                    self._cache['storage'][key] = StorageOption.objects.get(
                        plan_type=plan, 
                        storage_gb=storage_gb,
                        is_active=True
                    )
            except StorageOption.DoesNotExist:
                return None
        return self._cache['storage'].get(key)
    
    def _get_material(self, slug: str) -> Optional[PlaqueMaterial]:
        """Get material by slug with caching."""
        if slug not in self._cache.get('materials', {}):
            if 'materials' not in self._cache:
                self._cache['materials'] = {}
            try:
                self._cache['materials'][slug] = PlaqueMaterial.objects.get(slug=slug, is_active=True)
            except PlaqueMaterial.DoesNotExist:
                return None
        return self._cache['materials'].get(slug)
    
    def _get_addon(self, slug: str) -> Optional[Addon]:
        """Get addon by slug with caching."""
        if slug not in self._cache.get('addons', {}):
            if 'addons' not in self._cache:
                self._cache['addons'] = {}
            try:
                self._cache['addons'][slug] = Addon.objects.get(slug=slug, is_active=True)
            except Addon.DoesNotExist:
                return None
        return self._cache['addons'].get(slug)
    
    def _get_discount_rules(self) -> Dict[str, DiscountRule]:
        """Get all active discount rules."""
        if 'discounts' not in self._cache:
            self._cache['discounts'] = {
                d.slug: d for d in DiscountRule.objects.filter(is_active=True)
            }
        return self._cache['discounts']
    
    def get_copy_discount_rate(self, plaque_index: int) -> Decimal:
        """
        Get discount rate based on plaque position.
        - 1st plaque (index 0): Included in plan
        - 2nd plaque (index 1): second_copy discount
        - 3rd+ plaque (index 2+): third_plus_copy discount
        """
        if plaque_index == 0:
            return Decimal('0')
        
        discounts = self._get_discount_rules()
        
        if plaque_index == 1:
            rule = discounts.get('second_copy')
            return rule.discount_rate if rule else Decimal('0.30')
        
        rule = discounts.get('third_plus_copy')
        return rule.discount_rate if rule else Decimal('0.40')
    
    def get_bundle_discount_rate(self, complete_profile_count: int) -> Decimal:
        """
        Get bundle discount rate based on number of complete profiles.
        - 2 profiles: duo_bundle discount
        - 3+ profiles: family_bundle discount
        """
        discounts = self._get_discount_rules()
        
        if complete_profile_count >= 3:
            rule = discounts.get('family_bundle')
            return rule.discount_rate if rule else Decimal('0.20')
        elif complete_profile_count == 2:
            rule = discounts.get('duo_bundle')
            return rule.discount_rate if rule else Decimal('0.10')
        
        return Decimal('0')
    
    def calculate_plaque_price(
        self, 
        material_slug: str, 
        plaque_index: int,
        has_magnet: bool = False,
        has_engraving: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate the price for a single plaque.
        """
        material = self._get_material(material_slug)
        if not material:
            raise ValueError(f"Unknown material: {material_slug}")
        
        magnet_addon = self._get_addon('magnet')
        engraving_addon = self._get_addon('engraving')
        
        magnet_price = Decimal(magnet_addon.price if magnet_addon and has_magnet else 0)
        engraving_price = Decimal(engraving_addon.price if engraving_addon and has_engraving else 0)
        addons_total = magnet_price + engraving_price
        
        if plaque_index == 0:
            # First plaque: included, only upgrade cost
            return {
                'is_included': True,
                'base_price': Decimal('0'),
                'upgrade_price': material.upgrade_price,
                'discount_rate': Decimal('0'),
                'discount_amount': Decimal('0'),
                'discounted_price': material.upgrade_price,
                'magnet_price': magnet_price,
                'engraving_price': engraving_price,
                'addons_total': addons_total,
                'final_price': material.upgrade_price + addons_total,
            }
        else:
            # Additional plaques: apply copy discounts
            base_price = material.additional_price
            discount_rate = self.get_copy_discount_rate(plaque_index)
            discount_amount = base_price * discount_rate
            discounted_price = base_price - discount_amount
            
            return {
                'is_included': False,
                'base_price': base_price,
                'upgrade_price': Decimal('0'),
                'discount_rate': discount_rate,
                'discount_amount': discount_amount,
                'discounted_price': discounted_price,
                'magnet_price': magnet_price,
                'engraving_price': engraving_price,
                'addons_total': addons_total,
                'final_price': discounted_price + addons_total,
            }
    
    def calculate_profile_total(self, profile_data: Dict) -> Dict[str, Any]:
        """
        Calculate the total for a single profile.
        """
        plan_slug = profile_data.get('planType')
        storage_gb = Decimal(str(profile_data.get('storage', 1)))
        extension_years = profile_data.get('extensionYears', 0)
        plaques = profile_data.get('plaques', [])
        
        # Get plan and storage
        storage_option = self._get_storage_option(plan_slug, storage_gb)
        if not storage_option:
            raise ValueError(f"Invalid plan/storage combination: {plan_slug}/{storage_gb}")
        
        plan_cost = storage_option.price
        
        # Extension cost
        extension_addon = self._get_addon('extension')
        extension_cost = Decimal(extension_years) * (extension_addon.price if extension_addon else Decimal('49'))
        
        # Calculate plaque costs
        plaque_prices = []
        upgrade_cost = Decimal('0')
        additional_cost = Decimal('0')
        addons_cost = Decimal('0')
        copy_discount = Decimal('0')
        
        for index, plaque in enumerate(plaques):
            plaque_calc = self.calculate_plaque_price(
                material_slug=plaque.get('material', 'wood'),
                plaque_index=index,
                has_magnet=plaque.get('magnet', False),
                has_engraving=plaque.get('engraving', False)
            )
            
            plaque_prices.append(plaque_calc)
            
            if index == 0:
                upgrade_cost += plaque_calc['upgrade_price']
            else:
                additional_cost += plaque_calc['discounted_price']
                copy_discount += plaque_calc['discount_amount']
            
            addons_cost += plaque_calc['addons_total']
        
        total_plaque_cost = upgrade_cost + additional_cost + addons_cost
        subtotal = plan_cost + total_plaque_cost + extension_cost
        
        return {
            'plan_cost': plan_cost,
            'extension_cost': extension_cost,
            'extension_years': extension_years,
            'upgrade_cost': upgrade_cost,
            'additional_cost': additional_cost,
            'addons_cost': addons_cost,
            'total_plaque_cost': total_plaque_cost,
            'copy_discount': copy_discount,
            'subtotal': subtotal,
            'plaque_prices': plaque_prices,
            'is_complete': len(plaques) > 0,
        }
    
    def calculate_order_total(self, profiles_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate the complete order total with all discounts.
        """
        if not profiles_data:
            return {
                'plans_cost': Decimal('0'),
                'plaques_cost': Decimal('0'),
                'addons_cost': Decimal('0'),
                'extensions_cost': Decimal('0'),
                'subtotal': Decimal('0'),
                'copy_discount': Decimal('0'),
                'bundle_discount': Decimal('0'),
                'bundle_discount_rate': Decimal('0'),
                'shipping_cost': Decimal('0'),
                'total': Decimal('0'),
                'profile_count': 0,
                'complete_profile_count': 0,
                'profile_details': [],
            }
        
        plans_cost = Decimal('0')
        upgrade_cost = Decimal('0')
        additional_cost = Decimal('0')
        addons_cost = Decimal('0')
        extensions_cost = Decimal('0')
        copy_discount = Decimal('0')
        
        profile_details = []
        complete_count = 0
        
        for profile in profiles_data:
            calc = self.calculate_profile_total(profile)
            profile_details.append(calc)
            
            plans_cost += calc['plan_cost']
            upgrade_cost += calc['upgrade_cost']
            additional_cost += calc['additional_cost']
            addons_cost += calc['addons_cost']
            extensions_cost += calc['extension_cost']
            copy_discount += calc['copy_discount']
            
            if calc['is_complete']:
                complete_count += 1
        
        plaques_cost = upgrade_cost + additional_cost
        subtotal = plans_cost + plaques_cost + addons_cost + extensions_cost
        
        # Bundle discount
        bundle_discount_rate = self.get_bundle_discount_rate(complete_count)
        bundle_discount = subtotal * bundle_discount_rate
        
        # Shipping
        shipping_cost = self.config.shipping_cost
        if self.config.free_shipping_threshold:
            if subtotal >= self.config.free_shipping_threshold:
                shipping_cost = Decimal('0')
        
        total = subtotal - bundle_discount + shipping_cost
        
        return {
            'plans_cost': plans_cost,
            'plaques_cost': plaques_cost,
            'upgrade_cost': upgrade_cost,
            'additional_cost': additional_cost,
            'addons_cost': addons_cost,
            'extensions_cost': extensions_cost,
            'subtotal': subtotal,
            'copy_discount': copy_discount,
            'bundle_discount': bundle_discount,
            'bundle_discount_rate': bundle_discount_rate,
            'shipping_cost': shipping_cost,
            'total': total,
            'profile_count': len(profiles_data),
            'complete_profile_count': complete_count,
            'profile_details': profile_details,
        }


class OrderService:
    """
    Service for creating and managing orders.
    """
    
    def __init__(self):
        self.pricing = PricingService()
    
    @transaction.atomic
    def create_order(self, order_data: Dict, request=None) -> Order:
        """
        Create a new order from cart data.
        """
        profiles_data = order_data.get('profiles', [])
        
        # Calculate totals
        totals = self.pricing.calculate_order_total(profiles_data)
        
        # Create order
        order = Order.objects.create(
            customer_email=order_data.get('email'),
            customer_first_name=order_data.get('firstName'),
            customer_last_name=order_data.get('lastName'),
            customer_phone=order_data.get('phone', ''),
            shipping_address_line1=order_data.get('addressLine1'),
            shipping_address_line2=order_data.get('addressLine2', ''),
            shipping_city=order_data.get('city'),
            shipping_state=order_data.get('state', ''),
            shipping_postal_code=order_data.get('postalCode'),
            shipping_country=order_data.get('country', 'IT'),
            language=order_data.get('language', 'it'),
            subtotal=totals['subtotal'],
            plans_cost=totals['plans_cost'],
            plaques_cost=totals['plaques_cost'],
            addons_cost=totals['addons_cost'],
            copy_discount=totals['copy_discount'],
            bundle_discount=totals['bundle_discount'],
            bundle_discount_rate=totals['bundle_discount_rate'],
            shipping_cost=totals['shipping_cost'],
            total=totals['total'],
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
        )
        
        # Create profiles and plaques
        for idx, (profile_data, profile_calc) in enumerate(zip(profiles_data, totals['profile_details'])):
            plan_slug = profile_data.get('planType')
            storage_gb = Decimal(str(profile_data.get('storage', 1)))
            
            profile = OrderProfile.objects.create(
                order=order,
                name=profile_data.get('name', ''),
                plan_type=self.pricing._get_plan_type(plan_slug),
                plan_type_slug=plan_slug,
                storage_option=self.pricing._get_storage_option(plan_slug, storage_gb),
                storage_gb=storage_gb,
                plan_price=profile_calc['plan_cost'],
                extension_years=profile_calc['extension_years'],
                extension_price=profile_calc['extension_cost'],
                profile_subtotal=profile_calc['subtotal'],
                sort_order=idx,
            )
            
            # Create plaques
            plaques_data = profile_data.get('plaques', [])
            for plaque_idx, (plaque_data, plaque_calc) in enumerate(zip(plaques_data, profile_calc['plaque_prices'])):
                material_slug = plaque_data.get('material', 'wood')
                
                OrderPlaque.objects.create(
                    profile=profile,
                    material=self.pricing._get_material(material_slug),
                    material_slug=material_slug,
                    is_included=plaque_calc['is_included'],
                    base_price=plaque_calc['base_price'],
                    upgrade_price=plaque_calc['upgrade_price'],
                    discount_rate=plaque_calc['discount_rate'],
                    discount_amount=plaque_calc['discount_amount'],
                    has_magnet=plaque_data.get('magnet', False),
                    magnet_price=plaque_calc['magnet_price'],
                    has_engraving=plaque_data.get('engraving', False),
                    engraving_price=plaque_calc['engraving_price'],
                    final_price=plaque_calc['final_price'],
                    sort_order=plaque_idx,
                )
        
        # Record initial status
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status='pending',
            note='Order created'
        )
        
        return order
    
    def update_order_status(
        self, 
        order: Order, 
        new_status: str, 
        note: str = ''
    ) -> Order:
        """Update order status and record history."""
        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            note=note
        )
        
        return order
    
    def _get_client_ip(self, request) -> Optional[str]:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

