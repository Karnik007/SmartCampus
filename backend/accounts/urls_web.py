"""Accounts web (template) URL configuration."""

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('social-login/', views.social_login_web_view, name='social-login-web'),
]
