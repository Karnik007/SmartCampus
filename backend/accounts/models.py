"""
SmartCampus AI – Accounts Models
Custom User model with email-based auth and user profiles.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Custom manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Extended user model – email is the primary identifier."""

    PROVIDER_CHOICES = [
        ('email', 'Email'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('github', 'GitHub'),
    ]

    username = None  # Remove username field
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='email')
    provider_id = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    @property
    def first_name_display(self):
        return self.full_name.split(' ')[0] if self.full_name else self.email.split('@')[0]


class UserProfile(models.Model):
    """Extended profile with user preferences and defaults."""

    DIETARY_CHOICES = [
        ('all', 'All'),
        ('veg', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('non-veg', 'Non-Veg'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    campus_location = models.CharField(max_length=100, default='main')
    default_budget = models.IntegerField(default=250)
    dietary_preference = models.CharField(max_length=10, choices=DIETARY_CHOICES, default='all')
    interests = models.JSONField(default=list, blank=True)
    weight_price = models.IntegerField(default=50)
    weight_rating = models.IntegerField(default=70)
    weight_distance = models.IntegerField(default=40)
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'

    def __str__(self):
        return f"Profile: {self.user.email}"
