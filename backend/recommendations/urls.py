"""Recommendations API URL configuration."""

from django.urls import path
from . import views

app_name = 'recommendations_api'

urlpatterns = [
    path('recommend/', views.RecommendView.as_view(), name='recommend'),
    path('recommend/compare/', views.CompareView.as_view(), name='compare'),
    path('trust/', views.TrustScoreView.as_view(), name='trust-score'),
    path('items/food/', views.FoodItemListView.as_view(), name='food-list'),
    path('items/events/', views.EventListView.as_view(), name='event-list'),
]
