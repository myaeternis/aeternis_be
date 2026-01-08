"""
URL configuration for Aeternis Backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({'status': 'ok', 'service': 'aeternis-backend'})


def api_root(request):
    """API root with available endpoints."""
    return JsonResponse({
        'status': 'ok',
        'version': '1.0.0',
        'endpoints': {
            'pricing': '/api/pricing/',
            'orders': '/api/orders/',
            'payments': '/api/payments/',
            'admin': '/admin/',
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # API endpoints
    path('api/pricing/', include('pricing.urls', namespace='pricing')),
    path('api/orders/', include('orders.urls', namespace='orders')),
    path('api/payments/', include('payments.urls', namespace='payments')),
]

# Admin site customization
admin.site.site_header = 'Aeternis Administration'
admin.site.site_title = 'Aeternis Admin'
admin.site.index_title = 'Dashboard'
