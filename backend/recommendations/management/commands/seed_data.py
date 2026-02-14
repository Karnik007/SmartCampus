"""
Management command to seed the database with initial canteen, food, and event data.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from recommendations.models import Canteen, Tag, FoodItem, Event


CANTEENS = [
    {'name': 'Main Campus Canteen', 'campus_area': 'main'},
    {'name': 'Engineering Block Café', 'campus_area': 'engineering'},
    {'name': 'Food Court', 'campus_area': 'main'},
    {'name': 'Auditorium Hall A', 'campus_area': 'main'},
    {'name': 'Open Air Theatre', 'campus_area': 'main'},
    {'name': 'North Block Canteen', 'campus_area': 'north'},
    {'name': 'Sports Complex', 'campus_area': 'sports'},
    {'name': 'International Food Court', 'campus_area': 'main'},
]

TAGS = [
    ('Vegetarian', 'dietary'), ('Vegan', 'dietary'), ('Non-Veg', 'dietary'),
    ('South Indian', 'cuisine'), ('North Indian', 'cuisine'), ('Japanese', 'cuisine'),
    ('Healthy', 'other'), ('Quick Bite', 'other'), ('Biryani', 'cuisine'),
    ('Popular', 'other'), ('Spicy', 'other'), ('New Arrival', 'other'), ('Premium', 'other'),
    ('Tech', 'interest'), ('Networking', 'interest'), ('Workshop', 'interest'),
    ('Music', 'interest'), ('Cultural', 'interest'), ('Evening', 'other'),
    ('Sports', 'interest'), ('Competition', 'interest'), ('Free', 'other'),
]

FOOD_ITEMS = [
    {
        'name': 'South Indian Thali', 'price': 120, 'rating': 4.5, 'distance': 3,
        'dietary': 'veg', 'canteen': 'Main Campus Canteen', 'image': '🍛',
        'tags': ['Vegetarian', 'South Indian', 'Healthy'],
        'description': 'A complete traditional South Indian meal with rice, sambar, rasam, and sides.',
    },
    {
        'name': 'Veggie Wrap Combo', 'price': 90, 'rating': 4.2, 'distance': 5,
        'dietary': 'vegan', 'canteen': 'Engineering Block Café', 'image': '🌯',
        'tags': ['Vegan', 'Quick Bite', 'Healthy'],
        'description': 'Fresh veggie wrap with hummus and a side of salad.',
    },
    {
        'name': 'Chicken Biryani', 'price': 180, 'rating': 4.7, 'distance': 8,
        'dietary': 'non-veg', 'canteen': 'Food Court', 'image': '🍗',
        'tags': ['Non-Veg', 'Biryani', 'Popular'],
        'description': 'Fragrant basmati rice cooked with tender chicken and aromatic spices.',
    },
    {
        'name': 'Paneer Tikka Plate', 'price': 150, 'rating': 4.4, 'distance': 4,
        'dietary': 'veg', 'canteen': 'North Block Canteen', 'image': '🧀',
        'tags': ['Vegetarian', 'North Indian', 'Spicy'],
        'description': 'Marinated paneer cubes grilled to perfection with mint chutney.',
    },
    {
        'name': 'Sushi Platter (New!)', 'price': 250, 'rating': 4.9, 'distance': 12,
        'dietary': 'non-veg', 'canteen': 'International Food Court', 'image': '🍣',
        'tags': ['Japanese', 'New Arrival', 'Premium'],
        'description': 'Assorted sushi rolls with wasabi, ginger, and soy sauce. Limited-time campus special.',
        'is_featured': True,
    },
    {
        'name': 'Masala Dosa', 'price': 60, 'rating': 4.3, 'distance': 3,
        'dietary': 'veg', 'canteen': 'Main Campus Canteen', 'image': '🥞',
        'tags': ['Vegetarian', 'South Indian', 'Quick Bite'],
        'description': 'Crispy dosa with spiced potato filling, served with coconut chutney and sambar.',
    },
    {
        'name': 'Pasta Primavera', 'price': 130, 'rating': 4.1, 'distance': 5,
        'dietary': 'veg', 'canteen': 'Engineering Block Café', 'image': '🍝',
        'tags': ['Vegetarian', 'Healthy'],
        'description': 'Penne pasta with seasonal vegetables in a light garlic sauce.',
    },
    {
        'name': 'Fish & Chips', 'price': 200, 'rating': 4.5, 'distance': 8,
        'dietary': 'non-veg', 'canteen': 'Food Court', 'image': '🐟',
        'tags': ['Non-Veg', 'Popular'],
        'description': 'Crispy battered fish with golden fries and tartar sauce.',
    },
]

EVENTS = [
    {
        'name': 'Tech Innovation Summit', 'price': 50, 'rating': 4.8, 'distance': 10,
        'canteen': 'Auditorium Hall A', 'image': '💻',
        'tags': ['Tech', 'Networking', 'Workshop'],
        'description': 'Annual tech summit with keynotes, workshops, and networking. Includes hands-on sessions.',
    },
    {
        'name': 'Acoustic Night', 'price': 30, 'rating': 4.3, 'distance': 6,
        'canteen': 'Open Air Theatre', 'image': '🎵',
        'tags': ['Music', 'Cultural', 'Evening'],
        'description': 'Live acoustic performances by campus bands under the stars.',
    },
    {
        'name': 'Inter-College Sports Meet', 'price': 0, 'rating': 4.6, 'distance': 15,
        'canteen': 'Sports Complex', 'image': '⚽',
        'tags': ['Sports', 'Competition', 'Free'],
        'description': 'Annual inter-college sports competition. Participate or watch — your choice.',
    },
    {
        'name': 'AI & ML Workshop', 'price': 100, 'rating': 4.7, 'distance': 10,
        'canteen': 'Auditorium Hall A', 'image': '🤖',
        'tags': ['Tech', 'Workshop'],
        'description': 'Hands-on workshop on building ML models. Bring your laptop!',
    },
    {
        'name': 'Cultural Fest Dance Night', 'price': 80, 'rating': 4.5, 'distance': 6,
        'canteen': 'Open Air Theatre', 'image': '💃',
        'tags': ['Cultural', 'Music', 'Evening'],
        'description': 'Dance performances from various cultural groups. DJ after-party included.',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with initial canteen, food, and event data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')

        # Create canteens
        canteen_map = {}
        for c in CANTEENS:
            obj, created = Canteen.objects.get_or_create(
                name=c['name'], defaults={'campus_area': c['campus_area']}
            )
            canteen_map[c['name']] = obj
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  Canteen: {obj.name} [{status}]')

        # Create tags
        tag_map = {}
        for name, category in TAGS:
            obj, created = Tag.objects.get_or_create(
                name=name, defaults={'category': category}
            )
            tag_map[name] = obj

        self.stdout.write(f'  Tags: {len(tag_map)} ready')

        # Create food items
        for f in FOOD_ITEMS:
            canteen = canteen_map.get(f['canteen'])
            if not canteen:
                continue
            obj, created = FoodItem.objects.get_or_create(
                name=f['name'],
                defaults={
                    'price': f['price'],
                    'rating': f['rating'],
                    'distance': f['distance'],
                    'dietary': f['dietary'],
                    'canteen': canteen,
                    'image': f['image'],
                    'description': f.get('description', ''),
                    'is_featured': f.get('is_featured', False),
                }
            )
            if created:
                for tag_name in f.get('tags', []):
                    tag = tag_map.get(tag_name)
                    if tag:
                        obj.tags.add(tag)
            self.stdout.write(f'  Food: {obj.name} [{"Created" if created else "Exists"}]')

        # Create events
        for e in EVENTS:
            canteen = canteen_map.get(e['canteen'])
            if not canteen:
                continue
            obj, created = Event.objects.get_or_create(
                name=e['name'],
                defaults={
                    'price': e['price'],
                    'rating': e['rating'],
                    'distance': e['distance'],
                    'canteen': canteen,
                    'image': e['image'],
                    'description': e.get('description', ''),
                }
            )
            if created:
                for tag_name in e.get('tags', []):
                    tag = tag_map.get(tag_name)
                    if tag:
                        obj.tags.add(tag)
            self.stdout.write(f'  Event: {obj.name} [{"Created" if created else "Exists"}]')

        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
