"""
Admin configuration for Pricing models.
"""

from django.contrib import admin
from .models import (
    PlanType, StorageOption, PlaqueMaterial, 
    Addon, DiscountRule, PricingConfig
)


class StorageOptionInline(admin.TabularInline):
    model = StorageOption
    extra = 1
    fields = [
        'storage_gb', 'price', 'estimated_photos', 
        'estimated_video_minutes', 'estimated_audio_hours',
        'sort_order', 'is_active'
    ]


@admin.register(PlanType)
class PlanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'has_video', 'sort_order', 'is_active']
    list_filter = ['is_active', 'has_video']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [StorageOptionInline]
    fieldsets = (
        (None, {
            'fields': ('slug', 'name', 'description', 'has_video')
        }),
        ('Traduzioni', {
            'fields': (
                ('name_it', 'name_en', 'name_es'),
                ('description_it', 'description_en', 'description_es'),
            ),
            'classes': ('collapse',)
        }),
        ('Display', {
            'fields': ('icon', 'color_class', 'gradient_class', 'sort_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(StorageOption)
class StorageOptionAdmin(admin.ModelAdmin):
    list_display = [
        'plan_type', 'display_storage', 'price', 
        'estimated_photos', 'sort_order', 'is_active'
    ]
    list_filter = ['plan_type', 'is_active']
    list_editable = ['price', 'sort_order', 'is_active']
    ordering = ['plan_type', 'sort_order', 'storage_gb']


@admin.register(PlaqueMaterial)
class PlaqueMaterialAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'upgrade_price', 'additional_price', 
        'is_included', 'sort_order', 'is_active'
    ]
    list_filter = ['is_active', 'is_included']
    list_editable = ['upgrade_price', 'additional_price', 'sort_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('slug', 'name', 'is_included')
        }),
        ('Traduzioni', {
            'fields': (('name_it', 'name_en', 'name_es'),),
            'classes': ('collapse',)
        }),
        ('Prezzi', {
            'fields': ('upgrade_price', 'additional_price')
        }),
        ('Display', {
            'fields': ('icon', 'color_class', 'bg_color_class', 'sort_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'addon_type', 'price', 
        'applies_to_profile', 'applies_to_plaque', 'sort_order', 'is_active'
    ]
    list_filter = ['addon_type', 'is_active', 'applies_to_profile', 'applies_to_plaque']
    list_editable = ['price', 'sort_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('slug', 'addon_type', 'name', 'description')
        }),
        ('Traduzioni', {
            'fields': (
                ('name_it', 'name_en', 'name_es'),
                ('description_it', 'description_en', 'description_es'),
            ),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('price', 'extension_years')
        }),
        ('Applicazione', {
            'fields': ('applies_to_profile', 'applies_to_plaque')
        }),
        ('Display', {
            'fields': ('icon', 'sort_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'discount_type', 'discount_percentage',
        'min_items', 'max_items', 'priority', 'is_active'
    ]
    list_filter = ['discount_type', 'is_active']
    list_editable = ['discount_percentage', 'priority', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PricingConfig)
class PricingConfigAdmin(admin.ModelAdmin):
    list_display = [
        'currency', 'minimum_order_amount', 'shipping_cost', 
        'free_shipping_threshold', 'tax_rate', 'prices_include_tax'
    ]
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not PricingConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
