"""
URL configuration for the Orders API.
"""

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Calculate totals (validation)
    path('calculate/', views.CalculateTotalView.as_view(), name='calculate'),
    
    # Create order
    path('', views.CreateOrderView.as_view(), name='create'),
    
    # Get order by ID/number
    path('<str:order_id>/', views.OrderDetailView.as_view(), name='detail'),
    
    # Get orders by email
    path('by-email/', views.OrderByEmailView.as_view(), name='by-email'),
]

