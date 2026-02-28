"""Recommendations web (template) URL configuration."""

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/saved-places/', views.saved_places_view, name='saved-places'),
    path('dashboard/preferences/', views.preferences_view, name='preferences'),
    path('dashboard/history/', views.recommendation_history_view, name='recommendation-history'),
    path('results/', views.results_view, name='results'),
    path('trust/', views.trust_view, name='trust'),
    path('nearby/', views.nearby_view, name='nearby'),
    path('get-recommendations/', views.nearby_recommendations_api, name='get-recommendations'),
]
