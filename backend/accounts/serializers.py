"""
SmartCampus AI – Accounts Serializers
Handles user registration, login, profile, and social auth data validation.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, UserProfile


class SignupSerializer(serializers.ModelSerializer):
    """Registration serializer with password confirmation."""

    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
        )
        # Auto-create profile
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    """Email + password login."""

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Account is deactivated.')
        attrs['user'] = user
        return attrs


class SocialLoginSerializer(serializers.Serializer):
    """Social login – provider + token/email."""

    provider = serializers.ChoiceField(choices=['google', 'facebook', 'github'])
    email = serializers.EmailField()
    name = serializers.CharField(required=False, default='')
    provider_id = serializers.CharField(required=False, default='')
    avatar_url = serializers.URLField(required=False, allow_blank=True, default='')


class UserSerializer(serializers.ModelSerializer):
    """Public user data returned in auth responses."""

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'provider', 'avatar_url', 'is_verified', 'created_at']
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile for viewing/editing preferences."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'phone', 'campus_location', 'default_budget',
            'dietary_preference', 'interests', 'weight_price',
            'weight_rating', 'weight_distance', 'total_orders',
            'total_spent', 'created_at', 'updated_at',
        ]
        read_only_fields = ['total_orders', 'total_spent', 'created_at', 'updated_at']
