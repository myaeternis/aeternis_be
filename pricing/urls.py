"""
URL configuration for the Pricing API.
"""

from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    # Main pricing endpoint (all data)
    path('', views.PricingView.as_view(), name='pricing'),
    
    # Individual endpoints
    path('plans/', views.PlanTypesView.as_view(), name='plans'),
    path('materials/', views.MaterialsView.as_view(), name='materials'),
    path('addons/', views.AddonsView.as_view(), name='addons'),
    path('discounts/', views.DiscountsView.as_view(), name='discounts'),
]

