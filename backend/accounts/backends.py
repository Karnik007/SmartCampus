"""
Custom email authentication backend for CustomUser model.
Authenticates using email instead of username.
"""

from django.contrib.auth.backends import ModelBackend
from .models import CustomUser


class EmailBackend(ModelBackend):
    """Authenticate users by email address."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        # Also accept 'username' kwarg for compatibility with Django admin
        if email is None:
            email = kwargs.get('username')
        if email is None:
            return None
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
