/* ===================================================
   SmartCampus AI – Authentication Module (v2)
   Uses centralized SmartAPI client for JWT-based auth.
   No local fallbacks — all auth goes through Django.
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
    // NOTE: For template-served pages Django's @login_required handles this.
    // This JS guard is kept only for client-side UI (navbar display etc.)

    guard() {
        if (!this.isLoggedIn()) {
            sessionStorage.setItem('smartcampus-redirect', window.location.href);
            window.location.href = '/login/';
            return false;
        }
        return true;
    },

    _redirectAfterLogin() {
        const redirect = sessionStorage.getItem('smartcampus-redirect');
        sessionStorage.removeItem('smartcampus-redirect');
        window.location.href = redirect || '/dashboard/';
    },

    // ---- Email/Password Auth (API-based, used by social login buttons) ----

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
            const msg = err.detail || err.non_field_errors?.[0] || 'Login failed. Please check your credentials.';
            return { success: false, error: msg };
        }
    },

    // ---- Signup (API-based) ----

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
            const msg = err.detail || err.email?.[0] || err.non_field_errors?.[0] || 'Signup failed.';
            return { success: false, error: msg };
        }
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
        } catch (err) {
            const msg = err.detail || `${providerNames[provider]} login failed. Please try again.`;
            return { success: false, error: msg };
        }
    },

    // ---- Logout ----

    async logout() {
        try {
            await SmartAPI.logout();
        } catch { /* ignore */ }
        SmartAPI.clearTokens();
        localStorage.removeItem(this.STORAGE_KEY);
        // Redirect to Django's server-side logout to clear the session
        window.location.href = '/logout/';
    },
};
