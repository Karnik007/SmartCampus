"""Recommendations Admin configuration."""

from django.contrib import admin
from .models import Canteen, Tag, FoodItem, Event, UserPreference, RecommendationLog


@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ['name', 'campus_area', 'is_active']
    list_filter = ['campus_area', 'is_active']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'rating', 'dietary', 'canteen', 'is_available', 'is_featured', 'order_count']
    list_filter = ['dietary', 'is_available', 'is_featured', 'canteen']
    search_fields = ['name', 'description']
    filter_horizontal = ['tags']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'rating', 'canteen', 'is_active', 'event_date', 'registered_count']
    list_filter = ['is_active', 'canteen']
    search_fields = ['name', 'description']
    filter_horizontal = ['tags']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'budget', 'dietary', 'location', 'created_at']
    list_filter = ['dietary', 'location']


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_name', 'item_type', 'score', 'action', 'is_explore', 'created_at']
    list_filter = ['item_type', 'action', 'is_explore']
    search_fields = ['item_name', 'user__email']
