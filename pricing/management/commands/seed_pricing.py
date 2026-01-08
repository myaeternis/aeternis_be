"""
Management command to seed initial pricing data.

This command populates the database with the default pricing configuration
matching the frontend pricing.js file.

Usage:
    python manage.py seed_pricing
    python manage.py seed_pricing --clear  # Clear existing data first
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from pricing.models import (
    PlanType, StorageOption, PlaqueMaterial, 
    Addon, DiscountRule, PricingConfig
)


class Command(BaseCommand):
    help = 'Seed initial pricing data for Aeternis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing pricing data before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing pricing data...')
            StorageOption.objects.all().delete()
            PlanType.objects.all().delete()
            PlaqueMaterial.objects.all().delete()
            Addon.objects.all().delete()
            DiscountRule.objects.all().delete()
            PricingConfig.objects.all().delete()
        
        self.stdout.write('Seeding pricing data...')
        
        # Create PricingConfig
        self.create_config()
        
        # Create Plan Types and Storage Options
        self.create_plans()
        
        # Create Plaque Materials
        self.create_materials()
        
        # Create Add-ons
        self.create_addons()
        
        # Create Discount Rules
        self.create_discounts()
        
        self.stdout.write(self.style.SUCCESS('Pricing data seeded successfully!'))

    def create_config(self):
        config, created = PricingConfig.objects.get_or_create(
            pk=1,
            defaults={
                'currency': 'EUR',
                'currency_symbol': '€',
                'minimum_order_amount': Decimal('0.00'),
                'free_shipping_threshold': Decimal('100.00'),
                'shipping_cost': Decimal('0.00'),
                'tax_rate': Decimal('22.00'),
                'prices_include_tax': True,
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'  {action} PricingConfig')

    def create_plans(self):
        # MyAeternis Plan
        myaeternis, created = PlanType.objects.update_or_create(
            slug='myaeternis',
            defaults={
                'name': 'MyAeternis',
                'name_it': 'MyAeternis',
                'name_en': 'MyAeternis',
                'name_es': 'MyAeternis',
                'description': 'Piano digitale per foto e audio',
                'description_it': 'Piano digitale per foto e audio',
                'description_en': 'Digital plan for photos and audio',
                'description_es': 'Plan digital para fotos y audio',
                'has_video': False,
                'icon': 'Cloud',
                'color_class': 'text-blue-500',
                'gradient_class': 'from-blue-500 to-indigo-600',
                'sort_order': 1,
                'is_active': True,
            }
        )
        
        # MyAeternis storage options (prices include 1 wood plaque)
        myaeternis_storage = [
            {'gb': '0.25', 'price': '59', 'photos': 125, 'audio': 3},
            {'gb': '0.5', 'price': '69', 'photos': 250, 'audio': 7},
            {'gb': '1', 'price': '79', 'photos': 500, 'audio': 14},
            {'gb': '2', 'price': '99', 'photos': 1000, 'audio': 28},
            {'gb': '4', 'price': '119', 'photos': 2000, 'audio': 56},
        ]
        
        for idx, opt in enumerate(myaeternis_storage):
            StorageOption.objects.update_or_create(
                plan_type=myaeternis,
                storage_gb=Decimal(opt['gb']),
                defaults={
                    'price': Decimal(opt['price']),
                    'estimated_photos': opt['photos'],
                    'estimated_video_minutes': 0,
                    'estimated_audio_hours': opt['audio'],
                    'sort_order': idx,
                    'is_active': True,
                }
            )
        
        self.stdout.write(f'  Created PlanType: MyAeternis with {len(myaeternis_storage)} storage options')
        
        # Story Plan
        story, created = PlanType.objects.update_or_create(
            slug='story',
            defaults={
                'name': 'MyAeternis Story',
                'name_it': 'MyAeternis Story',
                'name_en': 'MyAeternis Story',
                'name_es': 'MyAeternis Story',
                'description': 'Piano digitale per foto, video e audio',
                'description_it': 'Piano digitale per foto, video e audio',
                'description_en': 'Digital plan for photos, video and audio',
                'description_es': 'Plan digital para fotos, video y audio',
                'has_video': True,
                'icon': 'BookOpen',
                'color_class': 'text-purple-500',
                'gradient_class': 'from-purple-500 to-pink-600',
                'sort_order': 2,
                'is_active': True,
            }
        )
        
        # Story storage options
        story_storage = [
            {'gb': '1', 'price': '109', 'photos': 500, 'video': 14, 'audio': 14},
            {'gb': '2', 'price': '129', 'photos': 1000, 'video': 28, 'audio': 28},
            {'gb': '4', 'price': '149', 'photos': 2000, 'video': 57, 'audio': 56},
            {'gb': '8', 'price': '189', 'photos': 4000, 'video': 114, 'audio': 110},
            {'gb': '16', 'price': '239', 'photos': 8000, 'video': 228, 'audio': 220},
        ]
        
        for idx, opt in enumerate(story_storage):
            StorageOption.objects.update_or_create(
                plan_type=story,
                storage_gb=Decimal(opt['gb']),
                defaults={
                    'price': Decimal(opt['price']),
                    'estimated_photos': opt['photos'],
                    'estimated_video_minutes': opt['video'],
                    'estimated_audio_hours': opt['audio'],
                    'sort_order': idx,
                    'is_active': True,
                }
            )
        
        self.stdout.write(f'  Created PlanType: Story with {len(story_storage)} storage options')

    def create_materials(self):
        materials = [
            {
                'slug': 'wood',
                'name': 'Legno',
                'name_it': 'Legno',
                'name_en': 'Wood',
                'name_es': 'Madera',
                'upgrade_price': '0',
                'additional_price': '34',
                'icon': 'TreeDeciduous',
                'color_class': 'text-amber-700',
                'bg_color_class': 'bg-amber-50',
                'is_included': True,
                'sort_order': 1,
            },
            {
                'slug': 'plexiglass',
                'name': 'Plexiglass',
                'name_it': 'Plexiglass',
                'name_en': 'Plexiglass',
                'name_es': 'Plexiglás',
                'upgrade_price': '15',
                'additional_price': '49',
                'icon': 'Square',
                'color_class': 'text-cyan-600',
                'bg_color_class': 'bg-cyan-50',
                'is_included': False,
                'sort_order': 2,
            },
            {
                'slug': 'brass',
                'name': 'Ottone',
                'name_it': 'Ottone',
                'name_en': 'Brass',
                'name_es': 'Latón',
                'upgrade_price': '35',
                'additional_price': '79',
                'icon': 'Award',
                'color_class': 'text-yellow-600',
                'bg_color_class': 'bg-yellow-50',
                'is_included': False,
                'sort_order': 3,
            },
        ]
        
        for mat in materials:
            PlaqueMaterial.objects.update_or_create(
                slug=mat['slug'],
                defaults={
                    'name': mat['name'],
                    'name_it': mat['name_it'],
                    'name_en': mat['name_en'],
                    'name_es': mat['name_es'],
                    'upgrade_price': Decimal(mat['upgrade_price']),
                    'additional_price': Decimal(mat['additional_price']),
                    'icon': mat['icon'],
                    'color_class': mat['color_class'],
                    'bg_color_class': mat['bg_color_class'],
                    'is_included': mat['is_included'],
                    'sort_order': mat['sort_order'],
                    'is_active': True,
                }
            )
        
        self.stdout.write(f'  Created {len(materials)} PlaqueMaterials')

    def create_addons(self):
        addons = [
            {
                'slug': 'extension',
                'addon_type': 'extension',
                'name': 'Estensione +10 anni',
                'name_it': 'Estensione +10 anni',
                'name_en': '+10 Years Extension',
                'name_es': 'Extensión +10 años',
                'description': 'Estendi la durata del tuo piano di altri 10 anni',
                'description_it': 'Estendi la durata del tuo piano di altri 10 anni',
                'description_en': 'Extend your plan duration by another 10 years',
                'description_es': 'Extiende la duración de tu plan otros 10 años',
                'price': '49',
                'extension_years': 10,
                'applies_to_profile': True,
                'applies_to_plaque': False,
                'icon': 'Clock',
                'sort_order': 1,
            },
            {
                'slug': 'magnet',
                'addon_type': 'magnet',
                'name': 'Fissaggio Magnetico',
                'name_it': 'Fissaggio Magnetico',
                'name_en': 'Magnetic Mount',
                'name_es': 'Montaje Magnético',
                'description': 'Sistema di fissaggio magnetico per la placca',
                'description_it': 'Sistema di fissaggio magnetico per la placca',
                'description_en': 'Magnetic mounting system for the plaque',
                'description_es': 'Sistema de montaje magnético para la placa',
                'price': '10',
                'extension_years': 0,
                'applies_to_profile': False,
                'applies_to_plaque': True,
                'icon': 'Magnet',
                'sort_order': 2,
            },
            {
                'slug': 'engraving',
                'addon_type': 'engraving',
                'name': 'Incisione Nome',
                'name_it': 'Incisione Nome',
                'name_en': 'Name Engraving',
                'name_es': 'Grabado de Nombre',
                'description': 'Incisione personalizzata del nome sulla placca',
                'description_it': 'Incisione personalizzata del nome sulla placca',
                'description_en': 'Custom name engraving on the plaque',
                'description_es': 'Grabado personalizado del nombre en la placa',
                'price': '19',
                'extension_years': 0,
                'applies_to_profile': False,
                'applies_to_plaque': True,
                'icon': 'Edit3',
                'sort_order': 3,
            },
        ]
        
        for addon in addons:
            Addon.objects.update_or_create(
                slug=addon['slug'],
                defaults={
                    'addon_type': addon['addon_type'],
                    'name': addon['name'],
                    'name_it': addon['name_it'],
                    'name_en': addon['name_en'],
                    'name_es': addon['name_es'],
                    'description': addon['description'],
                    'description_it': addon['description_it'],
                    'description_en': addon['description_en'],
                    'description_es': addon['description_es'],
                    'price': Decimal(addon['price']),
                    'extension_years': addon['extension_years'],
                    'applies_to_profile': addon['applies_to_profile'],
                    'applies_to_plaque': addon['applies_to_plaque'],
                    'icon': addon['icon'],
                    'sort_order': addon['sort_order'],
                    'is_active': True,
                }
            )
        
        self.stdout.write(f'  Created {len(addons)} Addons')

    def create_discounts(self):
        discounts = [
            {
                'slug': 'second_copy',
                'discount_type': 'copy_discount',
                'name': 'Sconto Seconda Copia',
                'description': '30% di sconto sulla seconda placca dello stesso profilo',
                'min_items': 2,
                'max_items': 2,
                'discount_percentage': '30',
                'priority': 10,
            },
            {
                'slug': 'third_plus_copy',
                'discount_type': 'copy_discount',
                'name': 'Sconto Terza Copia e Successive',
                'description': '40% di sconto dalla terza placca in poi dello stesso profilo',
                'min_items': 3,
                'max_items': None,
                'discount_percentage': '40',
                'priority': 20,
            },
            {
                'slug': 'duo_bundle',
                'discount_type': 'bundle_discount',
                'name': 'Duo Bundle',
                'description': '10% di sconto per 2 profili completi',
                'min_items': 2,
                'max_items': 2,
                'discount_percentage': '10',
                'priority': 5,
            },
            {
                'slug': 'family_bundle',
                'discount_type': 'bundle_discount',
                'name': 'Family Bundle',
                'description': '20% di sconto per 3 o più profili completi',
                'min_items': 3,
                'max_items': None,
                'discount_percentage': '20',
                'priority': 10,
            },
        ]
        
        for discount in discounts:
            DiscountRule.objects.update_or_create(
                slug=discount['slug'],
                defaults={
                    'discount_type': discount['discount_type'],
                    'name': discount['name'],
                    'description': discount['description'],
                    'min_items': discount['min_items'],
                    'max_items': discount['max_items'],
                    'discount_percentage': Decimal(discount['discount_percentage']),
                    'priority': discount['priority'],
                    'is_active': True,
                }
            )
        
        self.stdout.write(f'  Created {len(discounts)} DiscountRules')

