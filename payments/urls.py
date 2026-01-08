"""
URL configuration for the Payments API.
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Create checkout session
    path(
        'create-checkout-session/', 
        views.CreateCheckoutSessionView.as_view(), 
        name='create-checkout-session'
    ),
    
    # Get session status
    path(
        'session-status/', 
        views.CheckoutSessionStatusView.as_view(), 
        name='session-status'
    ),
    
    # Stripe webhook
    path(
        'webhook/', 
        views.StripeWebhookView.as_view(), 
        name='webhook'
    ),
    
    # Payment detail
    path(
        '<uuid:payment_id>/', 
        views.PaymentDetailView.as_view(), 
        name='detail'
    ),
]

