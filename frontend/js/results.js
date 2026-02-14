/* ===================================================
   SmartCampus AI – Results Page Logic (v2)
   Uses SmartAPI, adds "Order Now" functionality
   =================================================== */

// ---- Dummy Data (fallback when backend is down) ----
const DummyData = {
  recommendations: [
    {
      id: 1, name: "South Indian Thali", type: "food", price: 120, rating: 4.5,
      distance: 3, tags: ["Vegetarian", "South Indian", "Healthy"], dietary: "veg",
      image: "🍛", canteen: "Main Campus Canteen",
      reasons: [
        "Fits within your ₹{budget} budget",
        "Matches your vegetarian dietary preference",
        "High rating (4.5 stars)",
        "Close to your location (3 min walk)",
        "Popular among students with similar preferences"
      ]
    },
    {
      id: 2, name: "Veggie Wrap Combo", type: "food", price: 90, rating: 4.2,
      distance: 5, tags: ["Vegan", "Quick Bite", "Healthy"], dietary: "vegan",
      image: "🌯", canteen: "Engineering Block Café",
      reasons: [
        "Fits within your ₹{budget} budget",
        "Matches your vegan dietary preference",
        "High rating (4.2 stars)",
        "Quick meal option for busy schedules",
        "Highly rated by health-conscious students"
      ]
    },
    {
      id: 3, name: "Chicken Biryani", type: "food", price: 180, rating: 4.7,
      distance: 8, tags: ["Non-Veg", "Biryani", "Popular"], dietary: "non-veg",
      image: "🍗", canteen: "Food Court",
      reasons: [
        "Fits within your ₹{budget} budget",
        "Matches your non-veg dietary preference",
        "Highest rated item (4.7 stars)",
        "Most popular lunch choice on campus",
        "Great value for the portion size"
      ]
    },
    {
      id: 4, name: "Tech Innovation Summit", type: "event", price: 50, rating: 4.8,
      distance: 10, tags: ["Tech", "Networking", "Workshop"], dietary: "all",
      image: "💻", canteen: "Auditorium Hall A",
      reasons: [
        "Entry fee within your ₹{budget} budget",
        "Matches your interest in Tech Events",
        "Highest rated campus event (4.8 stars)",
        "Includes hands-on workshop session",
        "Great networking opportunity"
      ]
    },
    {
      id: 5, name: "Acoustic Night", type: "event", price: 30, rating: 4.3,
      distance: 6, tags: ["Music", "Cultural", "Evening"], dietary: "all",
      image: "🎵", canteen: "Open Air Theatre",
      reasons: [
        "Entry fee within your ₹{budget} budget",
        "Matches your interest in Music & Cultural events",
        "Highly rated by attendees (4.3 stars)",
        "Close to your location (6 min walk)",
        "Relaxing evening activity"
      ]
    },
    {
      id: 6, name: "Paneer Tikka Plate", type: "food", price: 150, rating: 4.4,
      distance: 4, tags: ["Vegetarian", "North Indian", "Spicy"], dietary: "veg",
      image: "🧀", canteen: "North Block Canteen",
      reasons: [
        "Fits within your ₹{budget} budget",
        "Matches your vegetarian dietary preference",
        "High rating (4.4 stars)",
        "Very close to your location (4 min walk)",
        "Chef's special today"
      ]
    },
    {
      id: 7, name: "Inter-College Sports Meet", type: "event", price: 0, rating: 4.6,
      distance: 15, tags: ["Sports", "Competition", "Free"], dietary: "all",
      image: "⚽", canteen: "Sports Complex",
      reasons: [
        "Free entry — fits any budget",
        "Matches your interest in Sports events",
        "Highly rated event (4.6 stars)",
        "Annual flagship event",
        "Participate or watch — your choice"
      ]
    }
  ],
  explore: {
    id: 99, name: "Sushi Platter (New!)", type: "food", price: 250, rating: 4.9,
    distance: 12, tags: ["Japanese", "New Arrival", "Premium"], dietary: "non-veg",
    image: "🍣", canteen: "International Food Court",
    reasons: [
      "You usually choose Indian cuisine — try something different!",
      "Highest rated new addition (4.9 stars)",
      "Within your budget",
      "Limited-time campus special",
      "Students who tried it loved it"
    ],
    exploreMessage: "You usually choose similar items. Try this highly rated alternative within your budget."
  }
};


// ---- Local API fallback ----
const LocalAPI = {
  filterLocal(prefs) {
    const budget = prefs.budget || 500;
    const dietary = prefs.dietary || 'all';
    const wP = (prefs.weight_price || prefs.weightPrice || 50) / 100;
    const wR = (prefs.weight_rating || prefs.weightRating || 70) / 100;
    const wD = (prefs.weight_distance || prefs.weightDistance || 40) / 100;

    let filtered = DummyData.recommendations.filter(item => {
      if (item.price > budget) return false;
      if (dietary !== 'all' && item.dietary !== 'all' && item.dietary !== dietary) return false;
      return true;
    });

    filtered.sort((a, b) => {
      const scoreA = (1 - a.price / 500) * wP + (a.rating / 5) * wR + (1 - a.distance / 20) * wD;
      const scoreB = (1 - b.price / 500) * wP + (b.rating / 5) * wR + (1 - b.distance / 20) * wD;
      return scoreB - scoreA;
    });

    filtered = filtered.slice(0, 5).map(item => ({
      ...item,
      score: Math.round(((1 - item.price / 500) * wP + (item.rating / 5) * wR + (1 - item.distance / 20) * wD) * 100),
      reasons: item.reasons.map(r => r.replace('{budget}', budget))
    }));

    const explore = {
      ...DummyData.explore,
      score: 88,
      reasons: DummyData.explore.reasons.map(r => r.replace('{budget}', budget))
    };

    return { recommendations: filtered, explore };
  }
};


// ---- UI Module ----
const UI = {
  compareList: [],
  _lastData: null,

  renderCards(data) {
    const grid = document.getElementById('resultsGrid');
    grid.innerHTML = '';

    data.recommendations.forEach(item => {
      const card = document.createElement('div');
      card.className = 'rec-card';
      card.setAttribute('data-id', item.id);
      card.innerHTML = `
        <div class="rec-card-header">
          <div class="rec-card-emoji">${item.image}</div>
          <div>
            <div class="rec-card-title">${item.name}</div>
            <div class="rec-card-canteen">${item.canteen}</div>
          </div>
        </div>
        <div class="rec-card-stats">
          <span class="rec-stat"><span class="rec-stat-icon">💰</span> ₹${item.price}</span>
          <span class="rec-stat"><span class="rec-stat-icon">⭐</span> ${item.rating}</span>
          <span class="rec-stat"><span class="rec-stat-icon">📍</span> ${item.distance} min</span>
          ${item.score ? `<span class="rec-stat"><span class="rec-stat-icon">📊</span> Score: ${item.score}%</span>` : ''}
        </div>
        <div class="rec-card-tags">
          ${item.tags.map(t => `<span class="rec-tag">${t}</span>`).join('')}
        </div>
        <div class="rec-card-actions">
          <button class="btn btn-sm btn-why" onclick="UI.toggleWhy(this)">Why This?</button>
          <button class="btn btn-sm btn-compare" data-id="${item.id}" onclick="UI.toggleCompare(this, ${item.id})">Compare</button>
          ${item.price > 0 ? `<button class="btn btn-sm btn-order" onclick="UI.orderItem(${JSON.stringify(item).replace(/"/g, '&quot;')})">🛒 Order</button>` : ''}
        </div>
        <div class="why-section">
          <div class="why-title">Why we recommended this:</div>
          <ul class="why-list">
            ${item.reasons.map(r => `<li class="why-item">${r}</li>`).join('')}
          </ul>
        </div>
      `;
      grid.appendChild(card);
    });
  },

  renderExplore(explore) {
    if (!explore) return;
    const container = document.getElementById('exploreCard');
    container.innerHTML = `
      <div class="explore-card">
        <div class="rec-card-header">
          <div class="rec-card-emoji">${explore.image}</div>
          <div>
            <div class="rec-card-title">${explore.name}</div>
            <div class="rec-card-canteen">${explore.canteen}</div>
          </div>
        </div>
        <div class="explore-message">${explore.exploreMessage || 'Try something different!'}</div>
        <div class="rec-card-stats">
          <span class="rec-stat"><span class="rec-stat-icon">💰</span> ₹${explore.price}</span>
          <span class="rec-stat"><span class="rec-stat-icon">⭐</span> ${explore.rating}</span>
          <span class="rec-stat"><span class="rec-stat-icon">📍</span> ${explore.distance} min</span>
          ${explore.score ? `<span class="rec-stat"><span class="rec-stat-icon">📊</span> Score: ${explore.score}%</span>` : ''}
        </div>
        <div class="rec-card-tags">
          ${explore.tags.map(t => `<span class="rec-tag">${t}</span>`).join('')}
        </div>
        <div class="rec-card-actions">
          <button class="btn btn-sm btn-why" onclick="UI.toggleWhy(this)">Why This?</button>
          ${explore.price > 0 ? `<button class="btn btn-sm btn-order" onclick="UI.orderItem(${JSON.stringify(explore).replace(/"/g, '&quot;')})">🛒 Order</button>` : ''}
        </div>
        <div class="why-section">
          <div class="why-title">Why we recommended this:</div>
          <ul class="why-list">
            ${explore.reasons.map(r => `<li class="why-item">${r}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  },

  toggleWhy(btn) {
    const card = btn.closest('.rec-card, .explore-card');
    const section = card.querySelector('.why-section');
    const expanded = section.classList.contains('expanded');
    section.classList.toggle('expanded');
    btn.textContent = expanded ? 'Why This?' : 'Hide Reasons';
  },

  toggleCompare(btn, id) {
    const idx = this.compareList.indexOf(id);
    if (idx > -1) {
      this.compareList.splice(idx, 1);
      btn.classList.remove('active');
      btn.textContent = 'Compare';
    } else {
      if (this.compareList.length >= 2) {
        Toast.show('You can only compare 2 items at a time.', '⚠️');
        return;
      }
      this.compareList.push(id);
      btn.classList.add('active');
      btn.textContent = 'Selected ✓';
    }
    if (this.compareList.length === 2) this.showComparison();
  },

  showComparison() {
    const allItems = [...this._lastData.recommendations];
    if (this._lastData.explore) allItems.push(this._lastData.explore);
    const items = this.compareList.map(id => allItems.find(i => i.id === id)).filter(Boolean);
    if (items.length < 2) { Toast.show('Could not find items.', '⚠️'); return; }

    document.getElementById('compareBody').innerHTML = `
      <div class="compare-grid">
        ${items.map(item => `
          <div class="compare-item">
            <div class="compare-item-emoji">${item.image}</div>
            <div class="compare-item-name">${item.name}</div>
            <div class="compare-row">
              <div class="compare-metric">
                <div class="compare-metric-label">Price</div>
                <div class="compare-metric-value">₹${item.price}</div>
              </div>
              <div class="compare-metric">
                <div class="compare-metric-label">Rating</div>
                <div class="compare-metric-value">⭐ ${item.rating} / 5</div>
              </div>
              <div class="compare-metric">
                <div class="compare-metric-label">Distance</div>
                <div class="compare-metric-value">📍 ${item.distance} min walk</div>
              </div>
              <div class="compare-metric">
                <div class="compare-metric-label">Tags</div>
                <div class="compare-tags">${item.tags.map(t => `<span class="rec-tag">${t}</span>`).join('')}</div>
              </div>
              <div class="compare-metric">
                <div class="compare-metric-label">Score</div>
                <div class="compare-score-bar"><div class="compare-score-fill" style="width:${item.score || 75}%;"></div></div>
                <div class="compare-metric-value" style="margin-top:4px;">${item.score || 75}%</div>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    document.getElementById('compareModal').classList.add('active');
  },

  closeComparison() {
    document.getElementById('compareModal').classList.remove('active');
    document.querySelectorAll('.btn-compare.active').forEach(btn => {
      btn.classList.remove('active');
      btn.textContent = 'Compare';
    });
    this.compareList = [];
  },

  // ---- Order item → redirect to payment page ----
  orderItem(item) {
    const orderData = {
      items: [{
        id: item.id,
        name: item.name,
        type: item.type,
        price: item.price,
        quantity: 1,
        image: item.image,
      }],
      total: item.price,
    };
    sessionStorage.setItem('smartcampus-order', JSON.stringify(orderData));
    window.location.href = 'payment.html';
  },
};


// ---- Page Init ----
document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.guard()) return;
  initShared();

  // Modal close handlers
  document.getElementById('modalClose').addEventListener('click', () => UI.closeComparison());
  document.getElementById('compareModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) UI.closeComparison();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') UI.closeComparison(); });

  // Load preferences from sessionStorage
  const raw = sessionStorage.getItem('smartcampus-prefs');
  const prefs = raw ? JSON.parse(raw) : {
    budget: 250, dietary: 'all', location: 'any', available_time: 30,
    interests: ['tech'], weight_price: 50, weight_rating: 70, weight_distance: 40
  };

  // Show loading
  Loader.show();
  await new Promise(r => setTimeout(r, 800));

  // Try backend API first, fallback to local
  let data;
  try {
    data = await SmartAPI.getRecommendations(prefs);
  } catch {
    data = LocalAPI.filterLocal(prefs);
  }

  Loader.hide();
  UI._lastData = data;
  UI.renderCards(data);
  UI.renderExplore(data.explore);
  Toast.show(`${data.recommendations.length} recommendations generated!`, '🎯');
});
