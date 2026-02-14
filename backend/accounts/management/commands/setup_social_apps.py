import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Setup social applications (Google, Facebook, GitHub) from environment variables'

    def handle(self, *args, **kwargs):
        # 1. Setup the Site
        # In dev, we use 127.0.0.1:8000
        site, created = Site.objects.update_or_create(
            id=1,
            defaults={
                'domain': '127.0.0.1:8000',
                'name': 'SmartCampus AI',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Site "{site.name}" ({site.domain}) configured.'))

        # 2. Setup Social Apps
        providers = [
            {
                'provider': 'google',
                'name': 'Google',
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            },
            {
                'provider': 'github',
                'name': 'GitHub',
                'client_id': os.getenv('GITHUB_CLIENT_ID'),
                'secret': os.getenv('GITHUB_CLIENT_SECRET'),
            },
            {
                'provider': 'facebook',
                'name': 'Facebook',
                'client_id': os.getenv('FACEBOOK_APP_ID'),
                'secret': os.getenv('FACEBOOK_APP_SECRET'),
            },
        ]

        for p in providers:
            if not p['client_id'] or not p['secret']:
                self.stdout.write(self.style.WARNING(f"Skipping {p['name']} - missing credentials in .env"))
                continue

            app, created = SocialApp.objects.update_or_create(
                provider=p['provider'],
                defaults={
                    'name': p['name'],
                    'client_id': p['client_id'],
                    'secret': p['secret'],
                }
            )
            app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f"SocialApp '{p['name']}' configured."))
