"""
SmartCampus AI – Accounts Forms
Django forms for server-side signup and login (template-based views).
"""

from django import forms
from .models import CustomUser


class SignupForm(forms.Form):
    """User registration form."""

    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'text-input',
            'placeholder': 'John Doe',
            'autocomplete': 'name',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'text-input',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'text-input',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        }),
    )
    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'text-input',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class LoginForm(forms.Form):
    """User login form."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'text-input',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'text-input',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
    )
