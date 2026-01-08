"""
API Views for Payments.
"""

import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from orders.models import Order
from orders.serializers import OrderSerializer
from .models import Payment
from .services import StripeService, WebhookHandler, PaymentError

logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(APIView):
    """
    POST /api/payments/create-checkout-session/
    
    Create a Stripe Checkout Session for an order.
    
    Request body:
    {
        "order_id": "uuid-or-order-number",
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }
    """
    
    def post(self, request):
        order_id = request.data.get('order_id')
        success_url = request.data.get('success_url')
        cancel_url = request.data.get('cancel_url')
        
        if not all([order_id, success_url, cancel_url]):
            return Response(
                {'error': 'Missing required fields: order_id, success_url, cancel_url'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find order
        try:
            try:
                order = Order.objects.get(pk=order_id)
            except (Order.DoesNotExist, ValueError):
                order = Order.objects.get(order_number=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check order status
        if order.status not in ['pending', 'payment_pending']:
            return Response(
                {'error': f'Order cannot be paid (status: {order.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stripe_service = StripeService()
            result = stripe_service.create_checkout_session(
                order=order,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            
            return Response(result)
            
        except PaymentError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CheckoutSessionStatusView(APIView):
    """
    GET /api/payments/session-status/?session_id=<session_id>
    
    Get the status of a checkout session.
    """
    
    def get(self, request):
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stripe_service = StripeService()
            result = stripe_service.get_session_status(session_id)
            
            # Also include order info if available
            try:
                payment = Payment.objects.get(stripe_checkout_session_id=session_id)
                result['order'] = OrderSerializer(payment.order).data
            except Payment.DoesNotExist:
                result['order'] = None
            
            return Response(result)
            
        except PaymentError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    POST /api/payments/webhook/
    
    Handle Stripe webhook events.
    This endpoint must be accessible without authentication.
    """
    
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        if not sig_header:
            logger.warning("Webhook received without signature")
            return Response(
                {'error': 'Missing signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        handler = WebhookHandler()
        
        try:
            event = handler.verify_and_construct_event(payload, sig_header)
            handler.handle_event(event)
            
            return Response({'status': 'success'})
            
        except PaymentError as e:
            logger.error(f"Webhook error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected webhook error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentDetailView(APIView):
    """
    GET /api/payments/<payment_id>/
    
    Get payment details.
    """
    
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(pk=payment_id)
            
            return Response({
                'id': str(payment.id),
                'order_id': str(payment.order.id),
                'order_number': payment.order.order_number,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'card_brand': payment.card_brand,
                'card_last4': payment.card_last4,
                'created_at': payment.created_at.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            })
            
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
