# SmartCampus AI

SmartCampus AI is a Django-based campus recommendation platform with:
- Email/social authentication
- Personalized recommendation APIs (food/events + nearby places)
- Server-rendered web UI with shared static assets

## Tech Stack
- Python, Django, Django REST Framework
- JWT (`djangorestframework-simplejwt`)
- django-allauth (Google/GitHub/Facebook)
- MySQL (default) or SQLite fallback
- Razorpay

## Project Structure
- `backend/`: Django project (source of truth for web + APIs + static assets)
- `frontend/`: static mirror for local experimentation (synced from `backend/static/js`)

## Local Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r backend/requirements.txt`
3. Create `backend/.env` (example keys):
   - `DEBUG=True`
   - `SECRET_KEY=<strong-random-secret>`
   - `ALLOWED_HOSTS=localhost,127.0.0.1`
   - `DB_ENGINE=django.db.backends.mysql` (or `django.db.backends.sqlite3`)
   - `DB_NAME=smartcamp_db`
   - `DB_USER=root`
   - `DB_PASSWORD=...`
   - `DB_HOST=127.0.0.1`
   - `DB_PORT=3306`
   - `CORS_ALLOWED_ORIGINS=http://localhost:8080`
   - `RAZORPAY_KEY_ID=...`
   - `RAZORPAY_KEY_SECRET=...`
   - `FOURSQUARE_API_KEY=...`
   - `EVENTBRITE_TOKEN=...`
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`
   - `GITHUB_CLIENT_ID=...`
   - `GITHUB_CLIENT_SECRET=...`
   - `FACEBOOK_APP_ID=...`
   - `FACEBOOK_APP_SECRET=...`

4. Run migrations:
   - `cd backend`
   - `python manage.py migrate`
5. Seed demo data:
   - `python manage.py seed_data`
6. Start server:
   - `python manage.py runserver`

## API Notes
- Base API path: `/api/`
- JWT refresh endpoint: `/api/auth/refresh/`
- Social API login now requires provider token(s), not client-asserted email:
  - `POST /api/auth/social/`
  - body: `{ "provider": "google|github|facebook", "access_token": "...", "id_token": "..." }`

## Security/Hardening Implemented
- Removed insecure hardcoded DB password default
- Enforced non-static `SECRET_KEY` behavior
- Added provider token verification for social login
- Removed CSRF-exempt nearby API flow; now session-auth + CSRF + rate-limited

## Validation
- `python manage.py check`
- `python manage.py test`
