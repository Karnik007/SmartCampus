"""
SmartCampus AI – Recommendations Views
API endpoints for getting recommendations, comparing items, and trust scores.
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.cache import cache

from .models import FoodItem, Event, UserPreference
from .serializers import (
    FoodItemSerializer, EventSerializer, PreferenceInputSerializer,
)
from . import engine

logger = logging.getLogger(__name__)


class RecommendView(APIView):
    """POST /api/recommend/ – Get personalized recommendations."""
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PreferenceInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prefs = serializer.validated_data

        # Save preference snapshot
        UserPreference.objects.create(
            user=request.user,
            budget=prefs['budget'],
            dietary=prefs['dietary'],
            location=prefs['location'],
            available_time=prefs['available_time'],
            interests=prefs['interests'],
            weight_price=prefs['weight_price'],
            weight_rating=prefs['weight_rating'],
            weight_distance=prefs['weight_distance'],
        )

        # Get recommendations
        recommendations = engine.get_recommendations(request.user, prefs)
        explore = engine.get_explore_item(request.user, prefs)

        logger.info(f"Generated {len(recommendations)} recommendations for {request.user.email}")

        return Response({
            'recommendations': recommendations,
            'explore': explore,
        })


class CompareView(APIView):
    """POST /api/recommend/compare/ – Compare two items."""
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        items_data = request.data.get('items', [])
        if len(items_data) != 2:
            return Response(
                {'error': 'Exactly 2 items required for comparison.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Items come pre-serialized from the frontend
        return Response({'items': items_data})


class SavePlaceView(APIView):
    """GET/POST /api/save-place/ – List or toggle save/unsave for items."""
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import SavedPlace
        places = list(
            SavedPlace.objects.filter(user=request.user)
            .order_by('-created_at')
            .values('item_type', 'item_id', 'item_name', 'created_at')
        )
        for p in places:
            if p.get('created_at'):
                p['created_at'] = p['created_at'].isoformat()
        return Response({'saved_places': places})

    def post(self, request):
        item_id = request.data.get('item_id')
        item_type = request.data.get('item_type')
        item_name = request.data.get('item_name', 'Unknown Item')

        if not item_id or item_type not in ['food', 'event']:
            return Response(
                {'error': 'Valid item_id and item_type (food/event) are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .models import SavedPlace
        
        # Toggle functionality
        saved_place = SavedPlace.objects.filter(
            user=request.user, 
            item_id=item_id, 
            item_type=item_type
        ).first()

        if saved_place:
            saved_place.delete()
            return Response({'status': 'unsaved', 'message': f'{item_name} removed from saved places.'})
        else:
            SavedPlace.objects.create(
                user=request.user,
                item_id=item_id,
                item_type=item_type,
                item_name=item_name
            )
            return Response({'status': 'saved', 'message': f'{item_name} saved successfully!'})


class TrustScoreView(APIView):
    """GET /api/trust/ – Get transparency/trust score breakdown."""
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trust = engine.compute_trust_score(request.user)
        return Response(trust)


class FoodItemListView(generics.ListAPIView):
    """GET /api/items/food/ – List all food items."""
    serializer_class = FoodItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['dietary', 'is_available', 'canteen']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'rating', 'distance']

    def get_queryset(self):
        return FoodItem.objects.filter(is_available=True).select_related('canteen').prefetch_related('tags')


class EventListView(generics.ListAPIView):
    """GET /api/items/events/ – List all events."""
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'rating', 'distance']

    def get_queryset(self):
        return Event.objects.filter(is_active=True).select_related('canteen').prefetch_related('tags')


# ============================================
# Template-based web views
# ============================================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    """GET /dashboard/ – Preferences form page."""
    return render(request, 'recommendations/dashboard.html')


@login_required
def saved_places_view(request):
    """GET /dashboard/saved-places/ – View saved places."""
    return render(request, 'recommendations/saved_places.html')


@login_required
def preferences_view(request):
    """GET /dashboard/preferences/ – User preferences page."""
    import json
    prefs = list(
        UserPreference.objects.filter(user=request.user)
        .order_by('-created_at')[:20]
        .values('budget', 'dietary', 'location', 'available_time',
                'interests', 'weight_price', 'weight_rating',
                'weight_distance', 'created_at')
    )
    # Convert datetimes to ISO strings for JSON
    for p in prefs:
        if p.get('created_at'):
            p['created_at'] = p['created_at'].isoformat()
    return render(request, 'recommendations/preferences.html', {
        'preferences_json': json.dumps(prefs),
    })


@login_required
def recommendation_history_view(request):
    """GET /dashboard/history/ – Recommendation history page."""
    import json
    from .models import RecommendationLog
    logs = list(
        RecommendationLog.objects.filter(user=request.user)
        .order_by('-created_at')[:50]
        .values('item_type', 'item_id', 'item_name', 'score',
                'action', 'is_explore', 'reasons', 'created_at')
    )
    for log in logs:
        if log.get('created_at'):
            log['created_at'] = log['created_at'].isoformat()
    return render(request, 'recommendations/recommendation_history.html', {
        'logs_json': json.dumps(logs),
    })


@login_required
@ensure_csrf_cookie
def results_view(request):
    """GET /results/ – Recommendation results page."""
    return render(request, 'recommendations/results.html')


@login_required
def trust_view(request):
    """GET /trust/ – Trust indicator page."""
    return render(request, 'recommendations/trust.html')


# ============================================
# Location-based nearby recommendations
# ============================================
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from recommendations.services.recommendation_service import get_nearby_recommendations


@login_required
def nearby_view(request):
    """GET /nearby/ – Redirect to merged results page."""
    from django.shortcuts import redirect
    return redirect('results')


def _too_many_requests(request) -> bool:
    """Simple per-minute limiter for nearby recommendation calls."""
    user_key = str(request.user.id) if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anon')
    cache_key = f"nearby_rate:{user_key}"
    count = cache.get(cache_key)
    if count is None:
        cache.set(cache_key, 1, timeout=60)
        return False
    if count >= 30:
        return True
    cache.incr(cache_key)
    return False


@login_required
@require_POST
def nearby_recommendations_api(request):
    """
    POST /get-recommendations/
    Body: { "latitude": float, "longitude": float, "preferences": [...] }
    Returns JSON list of scored nearby recommendations.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    lat = body.get("latitude")
    lon = body.get("longitude")

    # Validate coordinates
    if lat is None or lon is None:
        return JsonResponse({"error": "latitude and longitude are required."}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return JsonResponse({"error": "latitude and longitude must be numbers."}, status=400)

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return JsonResponse({"error": "Invalid coordinate range."}, status=400)

    preferences = body.get("preferences", [])
    if not isinstance(preferences, list):
        preferences = []
    accuracy_m = body.get("accuracy_m")
    try:
        accuracy_m = float(accuracy_m) if accuracy_m is not None else None
    except (TypeError, ValueError):
        accuracy_m = None

    if _too_many_requests(request):
        return JsonResponse({"error": "Rate limit exceeded. Please retry in a minute."}, status=429)

    try:
        results = get_nearby_recommendations(
            lat,
            lon,
            preferences or None,
            accuracy_m=accuracy_m,
        )
    except Exception as exc:
        logger.error("Recommendation engine error: %s", exc)
        return JsonResponse({"error": "Failed to fetch recommendations. Please try again."}, status=500)

    return JsonResponse(results, safe=False)
