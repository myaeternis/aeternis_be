"""
Order models for Aeternis.

Gestisce la struttura degli ordini con profili, placche e add-on.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from pricing.models import PlanType, StorageOption, PlaqueMaterial, Addon


class Order(models.Model):
    """
    Rappresenta un ordine completo.
    """
    STATUS_CHOICES = [
        ('pending', 'In attesa'),
        ('payment_pending', 'Pagamento in corso'),
        ('paid', 'Pagato'),
        ('processing', 'In lavorazione'),
        ('shipped', 'Spedito'),
        ('delivered', 'Consegnato'),
        ('cancelled', 'Annullato'),
        ('refunded', 'Rimborsato'),
    ]
    
    # Identificatori
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Customer info (no account required)
    customer_email = models.EmailField()
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=30, blank=True)
    
    # Shipping address
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=2, default='IT')
    
    # Order status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pricing snapshot (stored at time of order)
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    plans_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    plaques_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    addons_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    copy_discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    bundle_discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    bundle_discount_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    shipping_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(max_length=3, default='EUR')
    
    # Stripe
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Language preference
    language = models.CharField(max_length=5, default='it')
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Generate a unique order number."""
        import random
        import string
        from django.utils import timezone
        
        prefix = timezone.now().strftime('%y%m')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"AET-{prefix}-{suffix}"
    
    @property
    def profile_count(self):
        return self.profiles.count()
    
    @property
    def customer_full_name(self):
        return f"{self.customer_first_name} {self.customer_last_name}"


class OrderProfile(models.Model):
    """
    Un profilo all'interno di un ordine.
    Ogni profilo ha un piano digitale e una o più placche.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='profiles')
    
    # Profile info
    name = models.CharField(max_length=200, help_text="Nome della persona commemorata")
    
    # Plan selection (snapshot)
    plan_type = models.ForeignKey(
        PlanType, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='order_profiles'
    )
    plan_type_slug = models.CharField(max_length=50)  # Backup
    storage_option = models.ForeignKey(
        StorageOption,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_profiles'
    )
    storage_gb = models.DecimalField(max_digits=6, decimal_places=2)  # Backup
    plan_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Extension
    extension_years = models.PositiveIntegerField(default=0)
    extension_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Calculated totals for this profile
    profile_subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'sort_order']
        verbose_name = 'Order Profile'
        verbose_name_plural = 'Order Profiles'
    
    def __str__(self):
        return f"{self.name} - {self.order.order_number}"


class OrderPlaque(models.Model):
    """
    Una placca all'interno di un profilo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        OrderProfile, 
        on_delete=models.CASCADE, 
        related_name='plaques'
    )
    
    # Material (snapshot)
    material = models.ForeignKey(
        PlaqueMaterial,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_plaques'
    )
    material_slug = models.CharField(max_length=50)  # Backup
    
    # Pricing
    is_included = models.BooleanField(
        default=False,
        help_text="Prima placca inclusa nel piano"
    )
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Prezzo base (0 se inclusa)"
    )
    upgrade_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costo upgrade materiale"
    )
    discount_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sconto copia (0.30 = 30%)"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Add-ons
    has_magnet = models.BooleanField(default=False)
    magnet_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    has_engraving = models.BooleanField(default=False)
    engraving_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Final price for this plaque
    final_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['profile', 'sort_order']
        verbose_name = 'Order Plaque'
        verbose_name_plural = 'Order Plaques'
    
    def __str__(self):
        return f"{self.material_slug} plaque - {self.profile.name}"


class OrderStatusHistory(models.Model):
    """
    Storico dei cambiamenti di stato dell'ordine.
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status History'
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} -> {self.new_status}"
