"""
SmartCampus AI – Recommendations Models
Core data models for canteens, food items, events, preferences, and recommendation logs.
"""

from django.conf import settings
from django.db import models


class Canteen(models.Model):
    """A campus canteen or venue."""

    CAMPUS_AREA_CHOICES = [
        ('main', 'Main Campus'),
        ('engineering', 'Engineering Block'),
        ('north', 'North Block'),
        ('sports', 'Sports Complex'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    campus_area = models.CharField(max_length=30, choices=CAMPUS_AREA_CHOICES, default='main')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'canteens'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Categorization tag (e.g., Vegetarian, Tech, Music)."""

    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=[
        ('dietary', 'Dietary'),
        ('cuisine', 'Cuisine'),
        ('interest', 'Interest'),
        ('other', 'Other'),
    ], default='other')

    class Meta:
        db_table = 'tags'
        ordering = ['name']

    def __str__(self):
        return self.name


class FoodItem(models.Model):
    """A food item available in a campus canteen."""

    DIETARY_CHOICES = [
        ('veg', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('non-veg', 'Non-Veg'),
        ('all', 'All'),
    ]

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    rating = models.FloatField(default=0)
    rating_count = models.IntegerField(default=0)
    distance = models.IntegerField(help_text='Distance in minutes walk')
    dietary = models.CharField(max_length=10, choices=DIETARY_CHOICES, default='all')
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='food_items')
    tags = models.ManyToManyField(Tag, blank=True, related_name='food_items')
    image = models.CharField(max_length=10, default='🍽️', help_text='Emoji icon')
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'food_items'
        ordering = ['-rating', 'price']

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class Event(models.Model):
    """A campus event – tech talk, sports meet, cultural fest, etc."""

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    rating = models.FloatField(default=0)
    rating_count = models.IntegerField(default=0)
    distance = models.IntegerField(help_text='Distance in minutes walk')
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='events')
    tags = models.ManyToManyField(Tag, blank=True, related_name='events')
    image = models.CharField(max_length=10, default='📅', help_text='Emoji icon')
    description = models.TextField(blank=True)
    event_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    capacity = models.IntegerField(default=100)
    registered_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['-rating', 'price']

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class UserPreference(models.Model):
    """Snapshot of user preferences for a specific recommendation request."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    budget = models.IntegerField(default=250)
    dietary = models.CharField(max_length=10, default='all')
    location = models.CharField(max_length=50, default='any')
    available_time = models.IntegerField(default=30)
    interests = models.JSONField(default=list)
    weight_price = models.IntegerField(default=50)
    weight_rating = models.IntegerField(default=70)
    weight_distance = models.IntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_preferences'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pref: {self.user.email} @ ₹{self.budget}"


class RecommendationLog(models.Model):
    """Tracks what was recommended and how the user interacted."""

    ACTION_CHOICES = [
        ('shown', 'Shown'),
        ('clicked', 'Clicked'),
        ('ordered', 'Ordered'),
        ('dismissed', 'Dismissed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendation_logs')
    item_type = models.CharField(max_length=10, choices=[('food', 'Food'), ('event', 'Event')])
    item_id = models.IntegerField()
    item_name = models.CharField(max_length=255)
    score = models.FloatField(default=0)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='shown')
    is_explore = models.BooleanField(default=False, help_text='Was this an anti-filter-bubble suggestion')
    reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommendation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'item_type', 'action']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.item_name} ({self.action})"
