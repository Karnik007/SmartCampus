"""
SmartCampus AI – Accounts Views
JWT-based authentication endpoints: signup, login, social login, profile, logout.
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, UserProfile
from .serializers import (
    SignupSerializer, LoginSerializer, SocialLoginSerializer,
    UserSerializer, UserProfileSerializer,
)

logger = logging.getLogger(__name__)


def _get_tokens(user):
    """Generate JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class SignupView(APIView):
    """POST /api/auth/signup/ – Register a new user."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = _get_tokens(user)
        logger.info(f"New user registered: {user.email}")
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ – Email/password login."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = _get_tokens(user)
        logger.info(f"User logged in: {user.email}")
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        })


class SocialLoginView(APIView):
    """POST /api/auth/social/ – Social login (Google/Facebook/GitHub)."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Find or create user
        user, created = CustomUser.objects.get_or_create(
            email=data['email'],
            defaults={
                'full_name': data.get('name', ''),
                'provider': data['provider'],
                'provider_id': data.get('provider_id', ''),
                'avatar_url': data.get('avatar_url', ''),
                'is_verified': True,  # Social accounts are pre-verified
            }
        )

        if created:
            UserProfile.objects.create(user=user)
            logger.info(f"New social user created: {user.email} via {data['provider']}")
        else:
            # Update provider info if existing user
            if not user.provider_id and data.get('provider_id'):
                user.provider = data['provider']
                user.provider_id = data['provider_id']
                user.save(update_fields=['provider', 'provider_id'])

        tokens = _get_tokens(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/auth/profile/ – View or update user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class LogoutView(APIView):
    """POST /api/auth/logout/ – Blacklist the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.warning(f"Logout error: {e}")
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# Template-based web views (Django session auth)
# ============================================
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate as django_authenticate, login as django_login, logout as django_logout
from django.contrib import messages
from .forms import SignupForm, LoginForm


def signup_view(request):
    """GET/POST /signup/ – Server-rendered registration page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                full_name=form.cleaned_data['full_name'],
            )
            UserProfile.objects.create(user=user)
            django_login(request, user, backend='accounts.backends.EmailBackend')
            messages.success(request, f'Welcome, {user.first_name_display}!')
            logger.info(f"New user registered (web): {user.email}")
            return redirect('dashboard')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """GET/POST /login/ – Server-rendered login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Check if user exists first
            try:
                existing_user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                form.add_error(None, 'No account found with this email. Please sign up first.')
                return render(request, 'accounts/login.html', {'form': form})

            # User exists — verify password
            user = django_authenticate(request, email=email, password=password)
            if user is not None:
                django_login(request, user, backend='accounts.backends.EmailBackend')
                messages.success(request, f'Welcome back, {user.first_name_display}!')
                logger.info(f"User logged in (web): {user.email}")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                form.add_error(None, 'Incorrect password. Please try again.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """GET /logout/ – Log out and redirect to homepage."""
    django_logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_POST
def social_login_web_view(request):
    """POST /social-login/ – Social login that creates a Django session."""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    provider = data.get('provider', '')
    email = data.get('email', '')
    name = data.get('name', '')

    if not provider or not email:
        return JsonResponse({'success': False, 'error': 'Provider and email are required.'}, status=400)

    # Find or create user
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'full_name': name,
            'provider': provider,
            'is_verified': True,
        }
    )

    if created:
        UserProfile.objects.create(user=user)
        logger.info(f"New social user created (web): {user.email} via {provider}")

    # Create Django session
    django_login(request, user, backend='accounts.backends.EmailBackend')
    logger.info(f"Social login (web): {user.email} via {provider}")

    return JsonResponse({
        'success': True,
        'user': {
            'name': user.first_name_display,
            'email': user.email,
            'id': user.id,
        }
    })
