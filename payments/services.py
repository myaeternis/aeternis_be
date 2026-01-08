"""
Stripe payment services for Aeternis.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional, Any

import stripe
from django.conf import settings
from django.utils import timezone

from orders.models import Order
from orders.services import OrderService
from .models import Payment, StripeWebhookEvent

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """
    Service for Stripe payment operations.
    """
    
    def __init__(self):
        self.order_service = OrderService()
    
    def create_checkout_session(
        self, 
        order: Order,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session for an order.
        
        Args:
            order: The Order object
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
        
        Returns:
            Dict with checkout session details including URL
        """
        try:
            # Build line items from order
            line_items = self._build_line_items(order)
            
            # Create Stripe Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=line_items,
                customer_email=order.customer_email,
                client_reference_id=str(order.id),
                metadata={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                },
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                locale=self._get_stripe_locale(order.language),
                shipping_address_collection={
                    'allowed_countries': ['IT', 'DE', 'FR', 'ES', 'AT', 'CH', 'BE', 'NL'],
                },
                billing_address_collection='required',
                phone_number_collection={
                    'enabled': True,
                },
            )
            
            # Update order with session ID
            order.stripe_checkout_session_id = session.id
            order.status = 'payment_pending'
            order.save(update_fields=['stripe_checkout_session_id', 'status', 'updated_at'])
            
            # Create payment record
            Payment.objects.create(
                order=order,
                stripe_checkout_session_id=session.id,
                amount=order.total,
                currency=order.currency.lower(),
                status='pending',
            )
            
            logger.info(f"Created checkout session {session.id} for order {order.order_number}")
            
            return {
                'session_id': session.id,
                'url': session.url,
                'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise PaymentError(f"Payment service error: {str(e)}")
    
    def _build_line_items(self, order: Order) -> list:
        """
        Build Stripe line items from order.
        """
        line_items = []
        
        for profile in order.profiles.all():
            # Plan item
            plan_name = f"Piano {profile.plan_type_slug.title()} - {profile.storage_gb}GB"
            if profile.name:
                plan_name += f" ({profile.name})"
            
            line_items.append({
                'price_data': {
                    'currency': order.currency.lower(),
                    'unit_amount': int(profile.plan_price * 100),  # Stripe uses cents
                    'product_data': {
                        'name': plan_name,
                        'description': f'Piano digitale con {profile.storage_gb}GB di storage',
                    },
                },
                'quantity': 1,
            })
            
            # Extension if any
            if profile.extension_years > 0:
                line_items.append({
                    'price_data': {
                        'currency': order.currency.lower(),
                        'unit_amount': int(profile.extension_price * 100),
                        'product_data': {
                            'name': f'Estensione +{profile.extension_years * 10} anni',
                            'description': f'Estensione durata storage',
                        },
                    },
                    'quantity': 1,
                })
            
            # Plaques
            for plaque in profile.plaques.all():
                plaque_name = f"Placca {plaque.material_slug.title()}"
                if plaque.is_included:
                    plaque_name += " (inclusa)"
                
                # Only add if there's a cost
                plaque_base_cost = plaque.upgrade_price + (plaque.base_price - plaque.discount_amount)
                if plaque_base_cost > 0:
                    line_items.append({
                        'price_data': {
                            'currency': order.currency.lower(),
                            'unit_amount': int(plaque_base_cost * 100),
                            'product_data': {
                                'name': plaque_name,
                            },
                        },
                        'quantity': 1,
                    })
                
                # Add-ons
                if plaque.has_magnet and plaque.magnet_price > 0:
                    line_items.append({
                        'price_data': {
                            'currency': order.currency.lower(),
                            'unit_amount': int(plaque.magnet_price * 100),
                            'product_data': {
                                'name': 'Fissaggio Magnetico',
                            },
                        },
                        'quantity': 1,
                    })
                
                if plaque.has_engraving and plaque.engraving_price > 0:
                    line_items.append({
                        'price_data': {
                            'currency': order.currency.lower(),
                            'unit_amount': int(plaque.engraving_price * 100),
                            'product_data': {
                                'name': 'Incisione Nome',
                            },
                        },
                        'quantity': 1,
                    })
        
        # Bundle discount (as negative line item or coupon)
        if order.bundle_discount > 0:
            # We'll apply as a discount
            line_items.append({
                'price_data': {
                    'currency': order.currency.lower(),
                    'unit_amount': -int(order.bundle_discount * 100),
                    'product_data': {
                        'name': f'Sconto Bundle ({int(order.bundle_discount_rate * 100)}%)',
                    },
                },
                'quantity': 1,
            })
        
        # Shipping if any
        if order.shipping_cost > 0:
            line_items.append({
                'price_data': {
                    'currency': order.currency.lower(),
                    'unit_amount': int(order.shipping_cost * 100),
                    'product_data': {
                        'name': 'Spedizione',
                    },
                },
                'quantity': 1,
            })
        
        return line_items
    
    def _get_stripe_locale(self, language: str) -> str:
        """Map language code to Stripe locale."""
        locales = {
            'it': 'it',
            'en': 'en',
            'es': 'es',
            'de': 'de',
            'fr': 'fr',
        }
        return locales.get(language, 'auto')
    
    def handle_checkout_completed(self, session: dict) -> Payment:
        """
        Handle successful checkout completion.
        Called from webhook handler.
        """
        session_id = session['id']
        payment_intent_id = session.get('payment_intent')
        
        try:
            payment = Payment.objects.get(stripe_checkout_session_id=session_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for session {session_id}")
            raise PaymentError(f"Payment not found for session {session_id}")
        
        order = payment.order
        
        # Update payment
        payment.stripe_payment_intent_id = payment_intent_id
        payment.status = 'succeeded'
        payment.completed_at = timezone.now()
        payment.raw_response = session
        
        # Get card details if available
        if payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                if intent.charges and intent.charges.data:
                    charge = intent.charges.data[0]
                    payment.stripe_charge_id = charge.id
                    if charge.payment_method_details and charge.payment_method_details.card:
                        card = charge.payment_method_details.card
                        payment.card_brand = card.brand
                        payment.card_last4 = card.last4
                        payment.card_exp_month = card.exp_month
                        payment.card_exp_year = card.exp_year
            except stripe.error.StripeError as e:
                logger.warning(f"Could not retrieve payment intent details: {e}")
        
        payment.save()
        
        # Update order
        order.stripe_payment_intent_id = payment_intent_id
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save(update_fields=['stripe_payment_intent_id', 'status', 'paid_at', 'updated_at'])
        
        # Record status change
        self.order_service.update_order_status(
            order, 
            'paid', 
            f'Payment completed via Stripe (Session: {session_id})'
        )
        
        logger.info(f"Payment completed for order {order.order_number}")
        
        return payment
    
    def handle_payment_failed(self, session: dict) -> Payment:
        """
        Handle failed payment.
        """
        session_id = session['id']
        
        try:
            payment = Payment.objects.get(stripe_checkout_session_id=session_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for session {session_id}")
            raise PaymentError(f"Payment not found for session {session_id}")
        
        payment.status = 'failed'
        payment.raw_response = session
        payment.save()
        
        # Update order status back to pending
        order = payment.order
        self.order_service.update_order_status(order, 'pending', 'Payment failed')
        
        logger.warning(f"Payment failed for order {order.order_number}")
        
        return payment
    
    def create_refund(
        self, 
        payment: Payment, 
        amount: Optional[Decimal] = None,
        reason: str = ''
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment.
        
        Args:
            payment: The Payment object
            amount: Amount to refund (None for full refund)
            reason: Reason for refund
        
        Returns:
            Refund details
        """
        if not payment.can_refund:
            raise PaymentError("This payment cannot be refunded")
        
        refund_amount = amount or (payment.amount - payment.refunded_amount)
        
        try:
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=int(refund_amount * 100),
                reason='requested_by_customer',
                metadata={
                    'order_number': payment.order.order_number,
                    'reason': reason,
                },
            )
            
            # Update payment
            payment.refunded_amount += refund_amount
            if payment.refunded_amount >= payment.amount:
                payment.status = 'refunded'
            else:
                payment.status = 'partially_refunded'
            payment.save()
            
            # Update order if fully refunded
            if payment.status == 'refunded':
                self.order_service.update_order_status(
                    payment.order, 
                    'refunded', 
                    f'Full refund processed: {reason}'
                )
            
            logger.info(f"Refund of {refund_amount} processed for order {payment.order.order_number}")
            
            return {
                'refund_id': refund.id,
                'amount': float(refund_amount),
                'status': refund.status,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {e}")
            raise PaymentError(f"Refund failed: {str(e)}")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a checkout session.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'status': session.status,
                'payment_status': session.payment_status,
                'customer_email': session.customer_email,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            raise PaymentError(f"Could not retrieve session: {str(e)}")


class WebhookHandler:
    """
    Handler for Stripe webhooks.
    """
    
    def __init__(self):
        self.stripe_service = StripeService()
    
    def verify_and_construct_event(
        self, 
        payload: bytes, 
        sig_header: str
    ) -> stripe.Event:
        """
        Verify webhook signature and construct event.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise PaymentError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise PaymentError("Invalid signature")
    
    def handle_event(self, event: stripe.Event) -> bool:
        """
        Handle a Stripe webhook event.
        
        Returns:
            True if event was handled successfully
        """
        event_type = event['type']
        event_id = event['id']
        
        # Check for duplicate events (idempotency)
        if StripeWebhookEvent.objects.filter(stripe_event_id=event_id).exists():
            logger.info(f"Duplicate webhook event: {event_id}")
            return True
        
        # Create webhook event record
        webhook_event = StripeWebhookEvent.objects.create(
            stripe_event_id=event_id,
            event_type=event_type,
            payload=event.data.object,
        )
        
        try:
            # Handle specific event types
            if event_type == 'checkout.session.completed':
                session = event.data.object
                payment = self.stripe_service.handle_checkout_completed(session)
                webhook_event.payment = payment
                webhook_event.order = payment.order
                
            elif event_type == 'checkout.session.expired':
                session = event.data.object
                session_id = session['id']
                try:
                    payment = Payment.objects.get(stripe_checkout_session_id=session_id)
                    payment.status = 'cancelled'
                    payment.save()
                    webhook_event.payment = payment
                    webhook_event.order = payment.order
                except Payment.DoesNotExist:
                    pass
                
            elif event_type == 'payment_intent.payment_failed':
                intent = event.data.object
                try:
                    payment = Payment.objects.get(stripe_payment_intent_id=intent['id'])
                    payment.status = 'failed'
                    payment.error_code = intent.get('last_payment_error', {}).get('code', '')
                    payment.error_message = intent.get('last_payment_error', {}).get('message', '')
                    payment.save()
                    webhook_event.payment = payment
                    webhook_event.order = payment.order
                except Payment.DoesNotExist:
                    pass
            
            # Mark as processed
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            logger.info(f"Processed webhook event: {event_type} ({event_id})")
            return True
            
        except Exception as e:
            webhook_event.processing_error = str(e)
            webhook_event.save()
            logger.error(f"Error processing webhook {event_id}: {e}")
            raise


class PaymentError(Exception):
    """Custom exception for payment errors."""
    pass

