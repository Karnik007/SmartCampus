"""Recommendations serializers."""

from rest_framework import serializers
from .models import Canteen, Tag, FoodItem, Event, UserPreference


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'category']


class CanteenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Canteen
        fields = ['id', 'name', 'campus_area']


class FoodItemSerializer(serializers.ModelSerializer):
    canteen = CanteenSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'price', 'rating', 'distance', 'dietary',
            'canteen', 'tags', 'image', 'description', 'is_available',
            'is_featured', 'order_count',
        ]


class EventSerializer(serializers.ModelSerializer):
    canteen = CanteenSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'price', 'rating', 'distance', 'canteen',
            'tags', 'image', 'description', 'event_date', 'is_active',
            'capacity', 'registered_count',
        ]


class PreferenceInputSerializer(serializers.Serializer):
    """Validates user preferences for recommendation requests."""
    budget = serializers.IntegerField(min_value=0, max_value=10000, default=250)
    dietary = serializers.ChoiceField(
        choices=['all', 'veg', 'vegan', 'non-veg'],
        default='all'
    )
    location = serializers.CharField(max_length=50, default='any')
    available_time = serializers.IntegerField(min_value=5, max_value=360, default=30)
    interests = serializers.ListField(child=serializers.CharField(), default=list)
    weight_price = serializers.IntegerField(min_value=0, max_value=100, default=50)
    weight_rating = serializers.IntegerField(min_value=0, max_value=100, default=70)
    weight_distance = serializers.IntegerField(min_value=0, max_value=100, default=40)


class CompareInputSerializer(serializers.Serializer):
    """Validates comparison requests."""
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=2,
        max_length=2,
    )
