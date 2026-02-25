"""Recommendations web (template) URL configuration."""

from django.urls import path
from ..smartcampus import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('results/', views.results_view, name='results'),
    path('trust/', views.trust_view, name='trust'),
]
