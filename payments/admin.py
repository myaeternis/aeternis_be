"""
Admin configuration for Payment models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, StripeWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'order_link', 'amount_display', 
        'status_badge', 'card_display', 'created_at'
    ]
    list_filter = ['status', 'card_brand', 'created_at']
    search_fields = [
        'order__order_number', 'stripe_checkout_session_id',
        'stripe_payment_intent_id', 'card_last4'
    ]
    readonly_fields = [
        'id', 'order', 'stripe_checkout_session_id', 'stripe_payment_intent_id',
        'stripe_charge_id', 'amount', 'currency', 'status',
        'card_brand', 'card_last4', 'card_exp_month', 'card_exp_year',
        'error_code', 'error_message', 'refunded_amount',
        'raw_response', 'created_at', 'updated_at', 'completed_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('id', 'order', 'amount', 'currency', 'status')
        }),
        ('Stripe IDs', {
            'fields': (
                'stripe_checkout_session_id',
                'stripe_payment_intent_id',
                'stripe_charge_id'
            )
        }),
        ('Card Details', {
            'fields': ('card_brand', 'card_last4', 'card_exp_month', 'card_exp_year')
        }),
        ('Refund', {
            'fields': ('refunded_amount',)
        }),
        ('Errors', {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('raw_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def order_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'
    
    def amount_display(self, obj):
        return f"€{obj.amount:.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6b7280',
            'processing': '#f59e0b',
            'succeeded': '#10b981',
            'failed': '#ef4444',
            'cancelled': '#6b7280',
            'refunded': '#f97316',
            'partially_refunded': '#f97316',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def card_display(self, obj):
        if obj.card_brand and obj.card_last4:
            return f"{obj.card_brand.title()} •••• {obj.card_last4}"
        return "-"
    card_display.short_description = 'Card'


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        'stripe_event_id_short', 'event_type', 'order_link',
        'processed_badge', 'created_at'
    ]
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['stripe_event_id', 'event_type', 'order__order_number']
    readonly_fields = [
        'stripe_event_id', 'event_type', 'payment', 'order',
        'payload', 'processed', 'processing_error',
        'created_at', 'processed_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def stripe_event_id_short(self, obj):
        return obj.stripe_event_id[:20] + '...'
    stripe_event_id_short.short_description = 'Event ID'
    
    def order_link(self, obj):
        if obj.order:
            from django.urls import reverse
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return "-"
    order_link.short_description = 'Order'
    
    def processed_badge(self, obj):
        if obj.processed:
            return format_html(
                '<span style="color: #10b981;">✓</span>'
            )
        elif obj.processing_error:
            return format_html(
                '<span style="color: #ef4444;" title="{}">✗</span>',
                obj.processing_error[:100]
            )
        return format_html('<span style="color: #f59e0b;">⏳</span>')
    processed_badge.short_description = 'Processed'
