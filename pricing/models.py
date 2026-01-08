"""
Pricing models for Aeternis.

Gestione dinamica dei prezzi per:
- Piani digitali (MyAeternis, MyAeternis Story)
- Opzioni di storage
- Materiali placche
- Add-on (estensione, magnete, incisione)
- Sconti (copie, bundle)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class PlanType(models.Model):
    """
    Tipo di piano digitale (MyAeternis, Story, etc.)
    """
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    name_it = models.CharField(max_length=100, blank=True)
    name_en = models.CharField(max_length=100, blank=True)
    name_es = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    description_it = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    has_video = models.BooleanField(default=False)
    icon = models.CharField(max_length=50, default='Cloud')
    color_class = models.CharField(max_length=100, default='text-blue-500')
    gradient_class = models.CharField(max_length=100, default='from-blue-500 to-indigo-600')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Plan Type'
        verbose_name_plural = 'Plan Types'
    
    def __str__(self):
        return self.name
    
    def get_name(self, lang='it'):
        """Get localized name."""
        return getattr(self, f'name_{lang}', None) or self.name
    
    def get_description(self, lang='it'):
        """Get localized description."""
        return getattr(self, f'description_{lang}', None) or self.description


class StorageOption(models.Model):
    """
    Opzioni di storage per ogni tipo di piano.
    I prezzi includono 1 placca in legno.
    """
    plan_type = models.ForeignKey(
        PlanType, 
        on_delete=models.CASCADE, 
        related_name='storage_options'
    )
    storage_gb = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        help_text="Storage in GB (es. 0.25 per 250MB, 1 per 1GB)"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Prezzo in EUR (include 1 placca legno)"
    )
    # Stime capacità
    estimated_photos = models.PositiveIntegerField(default=0)
    estimated_video_minutes = models.PositiveIntegerField(default=0)
    estimated_audio_hours = models.PositiveIntegerField(default=0)
    
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['plan_type', 'sort_order', 'storage_gb']
        unique_together = ['plan_type', 'storage_gb']
        verbose_name = 'Storage Option'
        verbose_name_plural = 'Storage Options'
    
    def __str__(self):
        return f"{self.plan_type.name} - {self.display_storage}"
    
    @property
    def display_storage(self):
        """Format storage for display (250MB, 1GB, etc.)"""
        if self.storage_gb < 1:
            return f"{int(self.storage_gb * 1000)}MB"
        return f"{int(self.storage_gb)}GB"


class PlaqueMaterial(models.Model):
    """
    Materiali disponibili per le placche.
    """
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    name_it = models.CharField(max_length=100, blank=True)
    name_en = models.CharField(max_length=100, blank=True)
    name_es = models.CharField(max_length=100, blank=True)
    
    # Prezzo upgrade dalla placca inclusa (legno = 0)
    upgrade_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Costo upgrade dalla placca legno inclusa"
    )
    
    # Prezzo per copie aggiuntive
    additional_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Prezzo per placche aggiuntive (prima degli sconti)"
    )
    
    # Display properties
    icon = models.CharField(max_length=50, default='Square')
    color_class = models.CharField(max_length=100, default='text-gray-500')
    bg_color_class = models.CharField(max_length=100, default='bg-gray-50')
    
    is_included = models.BooleanField(
        default=False, 
        help_text="Materiale incluso nel piano base"
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Plaque Material'
        verbose_name_plural = 'Plaque Materials'
    
    def __str__(self):
        return self.name
    
    def get_name(self, lang='it'):
        """Get localized name."""
        return getattr(self, f'name_{lang}', None) or self.name


class Addon(models.Model):
    """
    Add-on disponibili (estensione, magnete, incisione).
    """
    ADDON_TYPES = [
        ('extension', 'Estensione durata'),
        ('magnet', 'Fissaggio magnetico'),
        ('engraving', 'Incisione nome'),
    ]
    
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    addon_type = models.CharField(max_length=20, choices=ADDON_TYPES)
    name = models.CharField(max_length=100)
    name_it = models.CharField(max_length=100, blank=True)
    name_en = models.CharField(max_length=100, blank=True)
    name_es = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    description_it = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Per estensione: numero di anni aggiuntivi
    extension_years = models.PositiveIntegerField(
        default=0,
        help_text="Anni aggiuntivi (solo per addon tipo extension)"
    )
    
    # Per quale entità si applica
    applies_to_profile = models.BooleanField(
        default=False,
        help_text="Si applica al profilo (es. estensione)"
    )
    applies_to_plaque = models.BooleanField(
        default=False,
        help_text="Si applica alla singola placca (es. magnete)"
    )
    
    icon = models.CharField(max_length=50, default='Plus')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Add-on'
        verbose_name_plural = 'Add-ons'
    
    def __str__(self):
        return f"{self.name} (€{self.price})"
    
    def get_name(self, lang='it'):
        return getattr(self, f'name_{lang}', None) or self.name
    
    def get_description(self, lang='it'):
        return getattr(self, f'description_{lang}', None) or self.description


class DiscountRule(models.Model):
    """
    Regole di sconto configurabili.
    """
    DISCOUNT_TYPES = [
        ('copy_discount', 'Sconto copie (stessa placca)'),
        ('bundle_discount', 'Sconto bundle (multi-profilo)'),
    ]
    
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Condizioni
    min_items = models.PositiveIntegerField(
        default=1,
        help_text="Numero minimo di elementi per attivare lo sconto"
    )
    max_items = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Numero massimo di elementi (null = illimitato)"
    )
    
    # Sconto
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Percentuale di sconto (es. 30 per 30%)"
    )
    
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Priorità (sconti con priorità maggiore si applicano prima)"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = 'Discount Rule'
        verbose_name_plural = 'Discount Rules'
    
    def __str__(self):
        return f"{self.name} (-{self.discount_percentage}%)"
    
    @property
    def discount_rate(self):
        """Return discount as decimal (0.30 for 30%)."""
        return self.discount_percentage / Decimal('100')


class PricingConfig(models.Model):
    """
    Configurazione globale dei prezzi.
    Singleton model per impostazioni generali.
    """
    currency = models.CharField(max_length=3, default='EUR')
    currency_symbol = models.CharField(max_length=5, default='€')
    
    # Importo minimo ordine
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Importo minimo ordine"
    )
    
    # Spedizione gratuita sopra un certo importo
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Soglia per spedizione gratuita"
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costo spedizione standard"
    )
    
    # Tax settings
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('22.00'),
        help_text="IVA in percentuale"
    )
    prices_include_tax = models.BooleanField(
        default=True,
        help_text="I prezzi già includono IVA"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pricing Configuration'
        verbose_name_plural = 'Pricing Configuration'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config
    
    def __str__(self):
        return f"Pricing Config ({self.currency})"
