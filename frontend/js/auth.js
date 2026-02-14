/* ===================================================
   SmartCampus AI – Authentication Module (v2)
   Uses centralized SmartAPI client for JWT-based auth.
   Falls back to localStorage simulation if backend is down.
   =================================================== */

const Auth = {
    STORAGE_KEY: 'smartcampus-user',

    // ---- Session helpers ----

    getUser() {
        try {
            const raw = localStorage.getItem(this.STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    },

    _saveUser(user) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(user));
    },

    isLoggedIn() {
        return this.getUser() !== null;
    },

    // ---- Route Guard ----

    guard() {
        if (!this.isLoggedIn()) {
            sessionStorage.setItem('smartcampus-redirect', window.location.href);
            window.location.href = 'login.html';
            return false;
        }
        return true;
    },

    _redirectAfterLogin() {
        const redirect = sessionStorage.getItem('smartcampus-redirect');
        sessionStorage.removeItem('smartcampus-redirect');
        window.location.href = redirect || 'dashboard.html';
    },

    // ---- Email/Password Auth ----

    async login(email, password) {
        if (!email || !password) {
            return { success: false, error: 'Please fill in all fields.' };
        }
        if (password.length < 6) {
            return { success: false, error: 'Password must be at least 6 characters.' };
        }

        try {
            const data = await SmartAPI.login(email, password);
            const user = {
                name: data.user.full_name || data.user.email.split('@')[0],
                email: data.user.email,
                avatar: data.user.avatar_url,
                provider: data.user.provider,
                id: data.user.id,
            };
            this._saveUser(user);
            return { success: true };
        } catch (err) {
            // Fallback to localStorage simulation
            if (err.status) {
                const msg = err.detail || err.non_field_errors?.[0] || 'Login failed.';
                return { success: false, error: msg };
            }
            return this._localLogin(email, password);
        }
    },

    _localLogin(email, password) {
        const users = JSON.parse(localStorage.getItem('smartcampus-users') || '[]');
        const existing = users.find(u => u.email === email);

        if (existing) {
            if (existing.password !== password) {
                return { success: false, error: 'Incorrect password.' };
            }
            const user = { name: existing.name, email: existing.email, avatar: null, provider: 'email' };
            this._saveUser(user);
            return { success: true };
        }
        return { success: false, error: 'No account found with this email. Please sign up.' };
    },

    // ---- Signup ----

    async signup(name, email, password, confirmPassword) {
        if (!name || !email || !password || !confirmPassword) {
            return { success: false, error: 'Please fill in all fields.' };
        }
        if (password.length < 6) {
            return { success: false, error: 'Password must be at least 6 characters.' };
        }
        if (password !== confirmPassword) {
            return { success: false, error: 'Passwords do not match.' };
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            return { success: false, error: 'Please enter a valid email address.' };
        }

        try {
            const data = await SmartAPI.signup(name, email, password, confirmPassword);
            const user = {
                name: data.user.full_name || name,
                email: data.user.email,
                avatar: data.user.avatar_url,
                provider: 'email',
                id: data.user.id,
            };
            this._saveUser(user);
            return { success: true };
        } catch (err) {
            if (err.status) {
                const msg = err.detail || err.email?.[0] || err.non_field_errors?.[0] || 'Signup failed.';
                return { success: false, error: msg };
            }
            return this._localSignup(name, email, password);
        }
    },

    _localSignup(name, email, password) {
        const users = JSON.parse(localStorage.getItem('smartcampus-users') || '[]');
        if (users.find(u => u.email === email)) {
            return { success: false, error: 'An account with this email already exists.' };
        }
        users.push({ name, email, password });
        localStorage.setItem('smartcampus-users', JSON.stringify(users));
        const user = { name, email, avatar: null, provider: 'email' };
        this._saveUser(user);
        return { success: true };
    },

    // ---- Social Login ----

    async socialLogin(provider) {
        const providerNames = { google: 'Google', facebook: 'Facebook', github: 'GitHub' };
        const providerEmails = {
            google: 'user@gmail.com',
            facebook: 'user@facebook.com',
            github: 'user@github.com',
        };

        try {
            const data = await SmartAPI.socialLogin(
                provider,
                providerEmails[provider],
                `${providerNames[provider]} User`
            );
            const user = {
                name: data.user.full_name || `${providerNames[provider]} User`,
                email: data.user.email,
                avatar: data.user.avatar_url,
                provider,
                id: data.user.id,
            };
            this._saveUser(user);
            return { success: true };
        } catch {
            // Fallback
            const user = {
                name: `${providerNames[provider]} User`,
                email: providerEmails[provider],
                avatar: null,
                provider,
            };
            this._saveUser(user);
            return { success: true };
        }
    },

    // ---- Logout ----

    async logout() {
        try {
            await SmartAPI.logout();
        } catch { /* ignore */ }
        SmartAPI.clearTokens();
        localStorage.removeItem(this.STORAGE_KEY);
        window.location.href = 'index.html';
    },
};
