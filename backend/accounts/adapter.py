"""
SmartCampus AI – Custom Allauth Adapter
Bridges django-allauth with the project's CustomUser model (email-based, no username).
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from accounts.models import UserProfile


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
    After social login, populate our custom fields and create a UserProfile.
    Also ensures the user is redirected to /dashboard/.
    """

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Populate custom fields from the social account data
        extra_data = sociallogin.account.extra_data
        provider = sociallogin.account.provider

        user.provider = provider
        user.provider_id = sociallogin.account.uid
        user.is_verified = True

        # Try to get a display name from the social data
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

        return user

    def get_login_redirect_url(self, request):
        return '/dashboard/'
