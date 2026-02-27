"""
SmartCampus AI – Custom Allauth Adapter
Bridges django-allauth with the project's CustomUser model (email-based, no username).
"""

import logging
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from accounts.models import CustomUser, UserProfile

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """Use email as the primary field, no username needed."""

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.full_name = user.first_name or user.email.split('@')[0]
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Handles social login for CustomUser (email-based, no username).
    - Auto-connects social accounts to existing users with matching email.
    - Populates custom fields from social provider data.
    - Creates UserProfile automatically.
    """

    def is_auto_signup_allowed(self, request, sociallogin):
        """Always allow auto signup for social accounts."""
        return True

    def pre_social_login(self, request, sociallogin):
        """
        If a user with this email already exists, connect the social
        account to that user instead of showing a signup form.
        """
        # If the social account is already linked to a user, nothing to do
        if sociallogin.is_existing:
            return

        # Get email from the social account
        email = None
        if sociallogin.user and sociallogin.user.email:
            email = sociallogin.user.email
        else:
            # Try to get email from extra_data
            extra_data = sociallogin.account.extra_data
            email = extra_data.get('email', '')

        if not email:
            return

        # Check if a user with this email already exists
        try:
            existing_user = CustomUser.objects.get(email=email)
            # Connect this social account to the existing user
            sociallogin.connect(request, existing_user)
            logger.info(f"Auto-connected {sociallogin.account.provider} to existing user {email}")
        except CustomUser.DoesNotExist:
            # No existing user — let allauth create one via auto_signup
            pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        self._populate_user_fields(user, sociallogin)
        return user

    def _populate_user_fields(self, user, sociallogin):
        """Populate custom fields from the social account data."""
        extra_data = sociallogin.account.extra_data
        provider = sociallogin.account.provider

        user.provider = provider
        user.provider_id = sociallogin.account.uid
        user.is_verified = True

        # Get display name from provider
        if provider == 'google':
            user.full_name = extra_data.get('name', '') or extra_data.get('given_name', '')
            user.avatar_url = extra_data.get('picture', '')
        elif provider == 'github':
            user.full_name = extra_data.get('name', '') or extra_data.get('login', '')
            user.avatar_url = extra_data.get('avatar_url', '')
        elif provider == 'facebook':
            user.full_name = extra_data.get('name', '')
        else:
            user.full_name = extra_data.get('name', user.email.split('@')[0])

        user.save()

        # Create UserProfile if it doesn't exist
        UserProfile.objects.get_or_create(user=user)

    def get_login_redirect_url(self, request):
        return '/dashboard/'
