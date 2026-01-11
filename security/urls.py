"""
URL configuration for Security endpoints.
"""

from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('challenge/', views.ChallengeView.as_view(), name='challenge'),
]
