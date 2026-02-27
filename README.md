
# 🚀 SmartCampusAI

An AI-powered real-time location-based recommendation system built with Django.

SmartCampusAI provides dynamic nearby recommendations including:

* 🍽 Restaurants & Cafes
* 🛍 Markets & Shops
* 🎮 Game Zones & Leisure Spots
* 🌳 Parks
* 🎉 Live Events

The system integrates multiple real-world APIs and applies intelligent ranking to deliver personalized recommendations.

---

## 🌍 Live Location-Based Recommendations

The engine uses:

* 🟢 OpenStreetMap (Overpass API) – Base venue data
* 🟢 Foursquare Places API – Enriched place details
* 🟢 Eventbrite API – Real-time nearby events

User GPS coordinates are captured via browser geolocation and sent securely to the backend.

---

## 🧠 Intelligent Scoring System

Each recommendation is ranked using a custom AI scoring algorithm:

```
score =
+3 if matches user preference
+2 if rating > 4
- (distance / 500)
+1 if open now
+2 if popular
```

Results are sorted by score and top recommendations are returned.

---

## 🏗 Project Architecture

```
smartcampus/
│
├── services/
│   └── recommendation_service.py
│
├── api_integrations/
│   ├── overpass.py
│   ├── foursquare.py
│   └── eventbrite.py
│
├── utils/
│   └── distance.py
│
├── templates/
├── static/
├── views.py
└── urls.py
```

---

## ⚙️ Tech Stack

* Python 3
* Django
* Vanilla JavaScript
* OpenStreetMap API
* Foursquare API
* Eventbrite API
* Django Cache Framework
* python-dotenv
* Haversine distance formula

---

## 🔐 Environment Variables

Create a `.env` file in project root:

```
FOURSQUARE_API_KEY=your_foursquare_key
EVENTBRITE_TOKEN=your_eventbrite_token
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project Locally

```bash
git clone https://github.com/your-username/SmartCampusAI.git
cd SmartCampusAI

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open:

```
http://127.0.0.1:8000/
```

---

## 📦 Key Features

* Real-time GPS-based recommendations
* Multi-API integration
* Modular backend architecture
* Distance calculation (Haversine)
* Smart ranking algorithm
* API key security via environment variables
* 5-minute location-based caching
* Dynamic frontend rendering

---

## 🚧 Future Improvements

* User preference learning
* Recommendation personalization history
* Async API calls (Celery / Redis)
* Deployment to AWS / Azure
* Real-time maps integration
* User analytics dashboard

---

## 👨‍💻 Author

Built as part of SmartCampusAI initiative.

---

---

# 💡 Optional Upgrade (If You Want It More Impressive)

If you want, I can:

* Add badges (Python, Django, License, etc.)
* Add screenshots section
* Add system architecture diagram
* Add deployment instructions
* Rewrite it more “startup style”
* Rewrite it more “research paper style”

Tell me what tone you want:

* 🔹 Clean professional
* 🔹 Startup pitch
* 🔹 Academic
* 🔹 Minimalistic
* 🔹 Aggressive portfolio mode 😄
