"""
Payment models for Aeternis.

Gestisce i record dei pagamenti Stripe.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from orders.models import Order


class Payment(models.Model):
    """
    Record di un pagamento.
    """
    STATUS_CHOICES = [
        ('pending', 'In attesa'),
        ('processing', 'In elaborazione'),
        ('succeeded', 'Completato'),
        ('failed', 'Fallito'),
        ('cancelled', 'Annullato'),
        ('refunded', 'Rimborsato'),
        ('partially_refunded', 'Parzialmente rimborsato'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    
    # Stripe IDs
    stripe_checkout_session_id = models.CharField(
        max_length=255, 
        blank=True, 
        db_index=True
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, 
        blank=True, 
        db_index=True
    )
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Card details (last 4 digits only for reference)
    card_brand = models.CharField(max_length=20, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
    card_exp_year = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # Error handling
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    
    # Refund tracking
    refunded_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Metadata
    raw_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment {self.id} - {self.order.order_number} ({self.status})"
    
    @property
    def is_successful(self):
        return self.status == 'succeeded'
    
    @property
    def can_refund(self):
        return self.status == 'succeeded' and self.refunded_amount < self.amount


class StripeWebhookEvent(models.Model):
    """
    Log of Stripe webhook events for debugging and idempotency.
    """
    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    
    # Related objects
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='webhook_events'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_events'
    )
    
    # Event data
    payload = models.JSONField(default=dict)
    
    # Processing status
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stripe Webhook Event'
        verbose_name_plural = 'Stripe Webhook Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"
