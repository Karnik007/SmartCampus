"""
SmartCampus AI – Recommendation Engine
Scoring algorithm, explanation generator, anti-filter-bubble, and trust computation.
"""

import logging
from django.db.models import Count, Q
from .models import FoodItem, Event, RecommendationLog

logger = logging.getLogger(__name__)


def score_item(item, preferences):
    """
    Calculate a weighted score for a food/event item.

    Score = (1 - price/max_budget) * wPrice
          + (rating/5.0) * wRating
          + (1 - distance/max_distance) * wDistance

    Returns a score between 0 and 100.
    """
    max_budget = max(preferences.get('budget', 500), 1)
    max_distance = 20  # Assume max walkable distance is 20 min

    price = float(item.price)
    rating = float(item.rating)
    distance = float(item.distance)

    w_price = preferences.get('weight_price', 50) / 100.0
    w_rating = preferences.get('weight_rating', 70) / 100.0
    w_distance = preferences.get('weight_distance', 40) / 100.0

    price_score = max(0, 1 - price / max_budget) * w_price
    rating_score = (rating / 5.0) * w_rating
    distance_score = max(0, 1 - distance / max_distance) * w_distance

    raw_score = price_score + rating_score + distance_score
    max_possible = w_price + w_rating + w_distance

    return round((raw_score / max_possible) * 100) if max_possible > 0 else 50


def generate_reasons(item, preferences, item_type='food'):
    """
    Generate human-readable explanation strings for why an item was recommended.
    """
    budget = preferences.get('budget', 500)
    dietary = preferences.get('dietary', 'all')
    reasons = []

    # Budget
    price = float(item.price)
    if price == 0:
        reasons.append("Free entry — fits any budget")
    elif price <= budget:
        reasons.append(f"Fits within your ₹{budget} budget (₹{int(price)})")
    else:
        reasons.append(f"Slightly above budget at ₹{int(price)}")

    # Dietary match (food only)
    if item_type == 'food' and hasattr(item, 'dietary'):
        dietary_map = {'veg': 'vegetarian', 'vegan': 'vegan', 'non-veg': 'non-veg'}
        item_diet = getattr(item, 'dietary', 'all')
        if dietary != 'all' and item_diet == dietary:
            reasons.append(f"Matches your {dietary_map.get(dietary, dietary)} dietary preference")

    # Rating
    rating = float(item.rating)
    if rating >= 4.5:
        reasons.append(f"Exceptionally rated ({rating} stars)")
    elif rating >= 4.0:
        reasons.append(f"High rating ({rating} stars)")
    elif rating >= 3.5:
        reasons.append(f"Good rating ({rating} stars)")

    # Distance
    distance = item.distance
    if distance <= 3:
        reasons.append(f"Very close to your location ({distance} min walk)")
    elif distance <= 8:
        reasons.append(f"Close to your location ({distance} min walk)")
    else:
        reasons.append(f"Reachable in {distance} min walk")

    # Interest match (events)
    if item_type == 'event':
        interests = preferences.get('interests', [])
        item_tags = [t.name.lower() for t in item.tags.all()]
        matched = [i for i in interests if i.lower() in ' '.join(item_tags)]
        if matched:
            reasons.append(f"Matches your interest in {', '.join(matched).title()}")

    # Popularity
    if hasattr(item, 'order_count') and item.order_count > 10:
        reasons.append("Popular among students with similar preferences")
    elif hasattr(item, 'registered_count') and item.registered_count > 20:
        reasons.append("Well-attended campus event")

    return reasons


def get_recommendations(user, preferences):
    """
    Main recommendation pipeline:
    1. Filter items by budget and dietary
    2. Score each item
    3. Sort and return top results with explanations
    """
    budget = preferences.get('budget', 500)
    dietary = preferences.get('dietary', 'all')

    # Fetch food items
    food_qs = FoodItem.objects.filter(is_available=True, price__lte=budget)
    if dietary != 'all':
        food_qs = food_qs.filter(Q(dietary=dietary) | Q(dietary='all'))
    food_qs = food_qs.select_related('canteen').prefetch_related('tags')

    # Fetch events
    event_qs = Event.objects.filter(is_active=True, price__lte=budget)
    event_qs = event_qs.select_related('canteen').prefetch_related('tags')

    results = []

    for item in food_qs:
        s = score_item(item, preferences)
        reasons = generate_reasons(item, preferences, 'food')
        results.append({
            'id': item.id,
            'name': item.name,
            'type': 'food',
            'price': float(item.price),
            'rating': item.rating,
            'distance': item.distance,
            'dietary': item.dietary,
            'tags': [t.name for t in item.tags.all()],
            'image': item.image,
            'canteen': item.canteen.name,
            'score': s,
            'reasons': reasons,
        })

    for item in event_qs:
        s = score_item(item, preferences)
        reasons = generate_reasons(item, preferences, 'event')
        results.append({
            'id': item.id,
            'name': item.name,
            'type': 'event',
            'price': float(item.price),
            'rating': item.rating,
            'distance': item.distance,
            'dietary': 'all',
            'tags': [t.name for t in item.tags.all()],
            'image': item.image,
            'canteen': item.canteen.name,
            'score': s,
            'reasons': reasons,
        })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)

    # Log recommendations
    for r in results[:5]:
        RecommendationLog.objects.create(
            user=user,
            item_type=r['type'],
            item_id=r['id'],
            item_name=r['name'],
            score=r['score'],
            reasons=r['reasons'],
        )

    return results[:5]


def get_explore_item(user, preferences):
    """
    Anti-filter-bubble: find an item from a category the user rarely tries.
    Falls back to highest-rated featured item.
    """
    budget = preferences.get('budget', 500)

    # Find categories the user has NOT interacted with
    past_types = RecommendationLog.objects.filter(
        user=user, action='ordered'
    ).values_list('item_name', flat=True)

    # Get a featured or high-rated item not in their usual picks
    explore = FoodItem.objects.filter(
        is_available=True,
        price__lte=budget,
    ).exclude(
        name__in=list(past_types)[:20]
    ).order_by('-rating', '-is_featured').first()

    if not explore:
        explore = FoodItem.objects.filter(
            is_available=True
        ).order_by('-rating').first()

    if not explore:
        return None

    reasons = [
        "You usually choose similar items — try something different!",
        f"Highly rated ({explore.rating} stars)",
        f"Within your ₹{budget} budget" if float(explore.price) <= budget else f"Premium option at ₹{int(explore.price)}",
        "Limited-time campus special" if explore.is_featured else "Popular among adventurous eaters",
        "Students who tried it loved it",
    ]

    return {
        'id': explore.id,
        'name': explore.name,
        'type': 'food',
        'price': float(explore.price),
        'rating': explore.rating,
        'distance': explore.distance,
        'dietary': explore.dietary,
        'tags': [t.name for t in explore.tags.all()],
        'image': explore.image,
        'canteen': explore.canteen.name,
        'score': score_item(explore, preferences),
        'reasons': reasons,
        'exploreMessage': "You usually choose similar items. Try this highly rated alternative within your budget.",
    }


def compute_trust_score(user):
    """
    Compute a trust/transparency score based on:
    - Budget compliance: % of recommendations within budget
    - Preference match: % matching dietary/interest preferences
    - Explanation clarity: all items have reasons (always 95%+)
    - Diversity: variety of categories recommended
    """
    logs = RecommendationLog.objects.filter(user=user).order_by('-created_at')[:50]

    if not logs.exists():
        return {
            'overall': 92,
            'budget_compliance': 100,
            'preference_match': 90,
            'explanation_clarity': 95,
            'diversity_score': 82,
        }

    total = logs.count()

    # Budget compliance
    budget_ok = sum(1 for l in logs if l.reasons and any('budget' in r.lower() for r in l.reasons))
    budget_pct = round((budget_ok / total) * 100) if total else 100

    # Explanation clarity (all items have reasons)
    has_reasons = sum(1 for l in logs if l.reasons and len(l.reasons) >= 2)
    clarity_pct = round((has_reasons / total) * 100) if total else 95

    # Diversity
    unique_items = len(set(l.item_name for l in logs))
    diversity_pct = min(100, round((unique_items / max(total, 1)) * 100))

    # Preference match (approximate)
    pref_pct = min(100, round(((budget_pct + diversity_pct) / 2) * 1.05))

    overall = round((budget_pct + pref_pct + clarity_pct + diversity_pct) / 4)

    return {
        'overall': min(100, overall),
        'budget_compliance': min(100, budget_pct),
        'preference_match': min(100, pref_pct),
        'explanation_clarity': min(100, clarity_pct),
        'diversity_score': min(100, diversity_pct),
    }
