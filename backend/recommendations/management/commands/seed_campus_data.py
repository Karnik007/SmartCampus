"""
SmartCampus AI – Seed Campus Data
Creates sample Canteens, Tags, and FoodItems so the local_food source
in the recommendation service returns results immediately.

Usage:
    python manage.py seed_campus_data
    python manage.py seed_campus_data --flush   # clear & re-create
"""

from django.core.management.base import BaseCommand
from recommendations.models import Canteen, Tag, FoodItem


# ── Canteen seed data ─────────────────────────────────────────────────
CANTEENS = [
    {"name": "Central Canteen",       "campus_area": "main",        "latitude": 18.5204, "longitude": 73.8567},
    {"name": "Engineering Mess",      "campus_area": "engineering", "latitude": 18.5190, "longitude": 73.8555},
    {"name": "North Block Café",      "campus_area": "north",       "latitude": 18.5215, "longitude": 73.8580},
    {"name": "Sports Complex Kiosk",  "campus_area": "sports",      "latitude": 18.5180, "longitude": 73.8590},
    {"name": "Library Corner Café",   "campus_area": "main",        "latitude": 18.5208, "longitude": 73.8572},
]

# ── Tag seed data ─────────────────────────────────────────────────────
TAGS = [
    {"name": "Vegetarian",  "category": "dietary"},
    {"name": "Vegan",       "category": "dietary"},
    {"name": "Non-Veg",     "category": "dietary"},
    {"name": "South Indian","category": "cuisine"},
    {"name": "North Indian","category": "cuisine"},
    {"name": "Chinese",     "category": "cuisine"},
    {"name": "Fast Food",   "category": "cuisine"},
    {"name": "Beverages",   "category": "cuisine"},
    {"name": "Healthy",     "category": "other"},
    {"name": "Budget",      "category": "other"},
    {"name": "Premium",     "category": "other"},
]

# ── FoodItem seed data: (canteen_index, attrs, tag_names) ─────────────
FOOD_ITEMS = [
    # Central Canteen
    (0, {"name": "Masala Dosa",        "price": 60,  "rating": 4.5, "distance": 3,  "dietary": "veg",     "image": "🫓", "description": "Crispy dosa with spicy potato filling", "order_count": 45}, ["Vegetarian", "South Indian"]),
    (0, {"name": "Paneer Butter Masala","price": 120, "rating": 4.3, "distance": 3,  "dietary": "veg",     "image": "🍛", "description": "Rich, creamy paneer curry", "order_count": 32}, ["Vegetarian", "North Indian"]),
    (0, {"name": "Chicken Biryani",    "price": 150, "rating": 4.6, "distance": 3,  "dietary": "non-veg", "image": "🍗", "description": "Aromatic rice with tender chicken", "order_count": 55}, ["Non-Veg", "North Indian"]),
    (0, {"name": "Cold Coffee",        "price": 50,  "rating": 4.2, "distance": 3,  "dietary": "veg",     "image": "☕", "description": "Chilled coffee with ice cream", "order_count": 60}, ["Vegetarian", "Beverages"]),

    # Engineering Mess
    (1, {"name": "Vada Pav",           "price": 25,  "rating": 4.4, "distance": 5,  "dietary": "veg",     "image": "🥙", "description": "Mumbai-style spicy potato fritter in bun", "order_count": 80}, ["Vegetarian", "Fast Food", "Budget"]),
    (1, {"name": "Samosa",             "price": 15,  "rating": 4.0, "distance": 5,  "dietary": "veg",     "image": "🥟", "description": "Crispy fried pastry with spicy filling", "order_count": 70}, ["Vegetarian", "Fast Food", "Budget"]),
    (1, {"name": "Egg Fried Rice",     "price": 80,  "rating": 4.1, "distance": 5,  "dietary": "non-veg", "image": "🍳", "description": "Stir-fried rice with scrambled eggs", "order_count": 25}, ["Non-Veg", "Chinese"]),
    (1, {"name": "Thali (Veg)",        "price": 100, "rating": 4.3, "distance": 5,  "dietary": "veg",     "image": "🍽️", "description": "Complete meal with roti, sabzi, dal, rice", "order_count": 40}, ["Vegetarian", "North Indian"]),

    # North Block Café
    (2, {"name": "Cappuccino",         "price": 80,  "rating": 4.5, "distance": 7,  "dietary": "veg",     "image": "☕", "description": "Italian-style coffee with foamed milk", "order_count": 35}, ["Vegetarian", "Beverages", "Premium"]),
    (2, {"name": "Grilled Sandwich",   "price": 70,  "rating": 4.2, "distance": 7,  "dietary": "veg",     "image": "🥪", "description": "Toasted sandwich with veggies and cheese", "order_count": 28}, ["Vegetarian", "Fast Food"]),
    (2, {"name": "Fruit Smoothie",     "price": 90,  "rating": 4.4, "distance": 7,  "dietary": "vegan",   "image": "🥤", "description": "Blended seasonal fruits with no sugar", "order_count": 20}, ["Vegan", "Beverages", "Healthy"]),

    # Sports Complex Kiosk
    (3, {"name": "Protein Shake",      "price": 120, "rating": 4.3, "distance": 10, "dietary": "veg",     "image": "💪", "description": "Whey protein shake with banana", "order_count": 15}, ["Vegetarian", "Beverages", "Healthy"]),
    (3, {"name": "Energy Bar",         "price": 50,  "rating": 3.8, "distance": 10, "dietary": "veg",     "image": "🍫", "description": "Oats and nuts energy bar", "order_count": 12}, ["Vegetarian", "Healthy", "Budget"]),
    (3, {"name": "Lemonade",           "price": 30,  "rating": 4.0, "distance": 10, "dietary": "vegan",   "image": "🍋", "description": "Fresh lime soda with mint", "order_count": 22}, ["Vegan", "Beverages", "Budget"]),

    # Library Corner Café
    (4, {"name": "Masala Chai",        "price": 20,  "rating": 4.6, "distance": 2,  "dietary": "veg",     "image": "🍵", "description": "Classic Indian spiced tea", "order_count": 90}, ["Vegetarian", "Beverages", "Budget"]),
    (4, {"name": "Maggi Noodles",      "price": 40,  "rating": 4.1, "distance": 2,  "dietary": "veg",     "image": "🍜", "description": "Quick noodles with veggies", "order_count": 65}, ["Vegetarian", "Fast Food", "Budget"]),
    (4, {"name": "Brownie",            "price": 60,  "rating": 4.4, "distance": 2,  "dietary": "veg",     "image": "🍫", "description": "Rich chocolate brownie", "order_count": 30}, ["Vegetarian", "Premium"]),
]


class Command(BaseCommand):
    help = "Seed the database with campus canteens, tags, and food items."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing seed data before re-creating.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            FoodItem.objects.all().delete()
            Canteen.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing data."))

        # 1. Tags
        tag_objects = {}
        for t in TAGS:
            obj, created = Tag.objects.get_or_create(name=t["name"], defaults={"category": t["category"]})
            tag_objects[t["name"]] = obj
            if created:
                self.stdout.write(f"  + Tag: {obj.name}")

        # 2. Canteens
        canteen_objects = []
        for c in CANTEENS:
            obj, created = Canteen.objects.get_or_create(
                name=c["name"],
                defaults={
                    "campus_area": c["campus_area"],
                    "latitude": c["latitude"],
                    "longitude": c["longitude"],
                },
            )
            canteen_objects.append(obj)
            if created:
                self.stdout.write(f"  + Canteen: {obj.name}")

        # 3. Food items
        created_count = 0
        for canteen_idx, attrs, tag_names in FOOD_ITEMS:
            canteen = canteen_objects[canteen_idx]
            obj, created = FoodItem.objects.get_or_create(
                name=attrs["name"],
                canteen=canteen,
                defaults=attrs,
            )
            if created:
                for tn in tag_names:
                    if tn in tag_objects:
                        obj.tags.add(tag_objects[tn])
                created_count += 1
                self.stdout.write(f"  + FoodItem: {obj.name} @ {canteen.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! {len(canteen_objects)} canteens, {len(tag_objects)} tags, "
                f"{created_count} new food items."
            )
        )
