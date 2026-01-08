"""
Admin configuration for Order models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderProfile, OrderPlaque, OrderStatusHistory


class OrderPlaqueInline(admin.TabularInline):
    model = OrderPlaque
    extra = 0
    readonly_fields = [
        'material_slug', 'is_included', 'base_price', 'upgrade_price',
        'discount_rate', 'discount_amount', 'has_magnet', 'magnet_price',
        'has_engraving', 'engraving_price', 'final_price'
    ]
    can_delete = False


class OrderProfileInline(admin.StackedInline):
    model = OrderProfile
    extra = 0
    readonly_fields = [
        'name', 'plan_type_slug', 'storage_gb', 'plan_price',
        'extension_years', 'extension_price', 'profile_subtotal'
    ]
    can_delete = False
    show_change_link = True


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'note', 'created_at']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_full_name', 'customer_email',
        'status_badge', 'total_display', 'profile_count', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'shipping_country']
    search_fields = ['order_number', 'customer_email', 'customer_first_name', 'customer_last_name']
    readonly_fields = [
        'id', 'order_number', 'customer_email', 'customer_first_name', 'customer_last_name',
        'customer_phone', 'shipping_address_line1', 'shipping_address_line2',
        'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country',
        'subtotal', 'plans_cost', 'plaques_cost', 'addons_cost',
        'copy_discount', 'bundle_discount', 'bundle_discount_rate',
        'shipping_cost', 'total', 'currency',
        'stripe_checkout_session_id', 'stripe_payment_intent_id',
        'ip_address', 'user_agent', 'created_at', 'updated_at', 'paid_at'
    ]
    inlines = [OrderProfileInline, OrderStatusHistoryInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('id', 'order_number', 'status', 'language')
        }),
        ('Customer', {
            'fields': (
                ('customer_first_name', 'customer_last_name'),
                'customer_email', 'customer_phone'
            )
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_address_line1', 'shipping_address_line2',
                ('shipping_city', 'shipping_state'),
                ('shipping_postal_code', 'shipping_country')
            )
        }),
        ('Pricing', {
            'fields': (
                ('plans_cost', 'plaques_cost', 'addons_cost'),
                'subtotal',
                ('copy_discount', 'bundle_discount', 'bundle_discount_rate'),
                'shipping_cost',
                ('total', 'currency')
            )
        }),
        ('Stripe', {
            'fields': ('stripe_checkout_session_id', 'stripe_payment_intent_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6b7280',
            'payment_pending': '#f59e0b',
            'paid': '#10b981',
            'processing': '#3b82f6',
            'shipped': '#8b5cf6',
            'delivered': '#059669',
            'cancelled': '#ef4444',
            'refunded': '#f97316',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_display(self, obj):
        return f"€{obj.total:.2f}"
    total_display.short_description = 'Total'


@admin.register(OrderProfile)
class OrderProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'plan_type_slug', 'storage_gb', 'profile_subtotal']
    list_filter = ['plan_type_slug']
    search_fields = ['name', 'order__order_number']
    readonly_fields = [
        'order', 'name', 'plan_type', 'plan_type_slug', 'storage_option',
        'storage_gb', 'plan_price', 'extension_years', 'extension_price',
        'profile_subtotal', 'created_at'
    ]
    inlines = [OrderPlaqueInline]


@admin.register(OrderPlaque)
class OrderPlaqueAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'material_slug', 'is_included', 
        'has_magnet', 'has_engraving', 'final_price'
    ]
    list_filter = ['material_slug', 'is_included', 'has_magnet', 'has_engraving']
    readonly_fields = [
        'profile', 'material', 'material_slug', 'is_included',
        'base_price', 'upgrade_price', 'discount_rate', 'discount_amount',
        'has_magnet', 'magnet_price', 'has_engraving', 'engraving_price',
        'final_price', 'created_at'
    ]
