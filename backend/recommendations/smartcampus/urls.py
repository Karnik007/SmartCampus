"""
SmartCampus AI – Root URL Configuration
API endpoints under /api/  |  Template pages at root level
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Homepage view
def homepage(request):
    return render(request, 'index.html')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # ---- Template (web) routes ----
    path('', homepage, name='home'),
    path('', include('accounts.urls_web')),
    path('', include('recommendations.urls_web')),
    path('', include('payments.urls_web')),

    # ---- Allauth (social OAuth) routes ----
    path('accounts/', include('allauth.urls')),

    # ---- API routes (existing) ----
    path('api/auth/', include('accounts.urls')),
    path('api/', include('recommendations.urls')),
    path('api/payment/', include('payments.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
