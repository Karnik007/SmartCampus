/* ===================================================
   SmartCampus AI – Centralized API Client
   JWT token management, auto-refresh, and API helpers
   =================================================== */

const API_BASE = '/api';

const SmartAPI = {

    // ---- Token Management ----

    getTokens() {
        try {
            const raw = localStorage.getItem('smartcampus-tokens');
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    },

    saveTokens(tokens) {
        localStorage.setItem('smartcampus-tokens', JSON.stringify(tokens));
    },

    clearTokens() {
        localStorage.removeItem('smartcampus-tokens');
    },

    getAccessToken() {
        const tokens = this.getTokens();
        return tokens ? tokens.access : null;
    },

    // ---- Auto-refresh on 401 ----

    async refreshToken() {
        const tokens = this.getTokens();
        if (!tokens || !tokens.refresh) return null;

        try {
            const res = await fetch(`${API_BASE}/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: tokens.refresh }),
            });
            if (!res.ok) throw new Error('Refresh failed');
            const data = await res.json();
            this.saveTokens({ access: data.access, refresh: data.refresh || tokens.refresh });
            return data.access;
        } catch {
            this.clearTokens();
            Auth.logout();
            return null;
        }
    },

    // ---- Core fetch wrapper ----

    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const token = this.getAccessToken();

        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        let res = await fetch(url, { ...options, headers });

        // Auto-refresh on 401
        if (res.status === 401 && token) {
            const newToken = await this.refreshToken();
            if (newToken) {
                headers['Authorization'] = `Bearer ${newToken}`;
                res = await fetch(url, { ...options, headers });
            }
        }

        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: 'Request failed' }));
            throw { status: res.status, ...error };
        }

        return res.json();
    },

    // ---- Convenience methods ----

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // ---- Auth helpers ----

    async login(email, password) {
        const data = await this.post('/auth/login/', { email, password });
        this.saveTokens(data.tokens);
        return data;
    },

    async signup(name, email, password, confirmPassword) {
        const data = await this.post('/auth/signup/', {
            email,
            full_name: name,
            password,
            confirm_password: confirmPassword,
        });
        this.saveTokens(data.tokens);
        return data;
    },

    async socialLogin(provider, email, name) {
        const data = await this.post('/auth/social/', { provider, email, name });
        this.saveTokens(data.tokens);
        return data;
    },

    async logout() {
        const tokens = this.getTokens();
        try {
            if (tokens && tokens.refresh) {
                await this.post('/auth/logout/', { refresh: tokens.refresh });
            }
        } catch { /* ignore logout errors */ }
        this.clearTokens();
    },

    async getProfile() {
        return this.get('/auth/profile/');
    },

    async updateProfile(data) {
        return this.put('/auth/profile/', data);
    },

    // ---- Recommendations ----

    async getRecommendations(prefs) {
        return this.post('/recommend/', prefs);
    },

    async getTrustScore() {
        return this.get('/trust/');
    },

    async toggleSavePlace(itemId, itemType, itemName) {
        return this.post('/save-place/', {
            item_id: itemId,
            item_type: itemType,
            item_name: itemName
        });
    }
};
