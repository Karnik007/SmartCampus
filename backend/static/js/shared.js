/* ===================================================
   SmartCampus AI – Shared Components
   Navbar injection, Theme, Toast, Loader
   Loaded on EVERY page.
   =================================================== */

// ==========================================
// MODULE: Navbar – inject shared navigation
// ==========================================
const Navbar = {
  /**
   * Inject the navbar HTML and wire up events.
   * Call this on DOMContentLoaded from every page.
   */
  init() {
    const user = Auth.getUser();
    const currentPage = window.location.pathname;

    const navHTML = `
    <nav class="navbar" id="navbar">
      <div class="nav-container">
        <a href="/" class="nav-logo">
          <span class="logo-icon">🎓</span>
          <span class="logo-text">SmartCampus<span class="logo-accent">AI</span></span>
        </a>
        <ul class="nav-links" id="navLinks">
          <li><a href="/" ${currentPage === '/' ? 'class="active"' : ''}>Home</a></li>
          <li><a href="/dashboard/" ${currentPage === '/dashboard/' ? 'class="active"' : ''}>Dashboard</a></li>
          <li><a href="/results/" ${currentPage === '/results/' ? 'class="active"' : ''}>Results</a></li>
          <li><a href="/trust/" ${currentPage === '/trust/' ? 'class="active"' : ''}>Trust</a></li>
          <li><a href="/payment/" ${currentPage === '/payment/' ? 'class="active"' : ''}>Payment</a></li>
        </ul>
        <div class="nav-actions">
          <button class="theme-toggle" id="themeToggle" aria-label="Toggle dark/light mode">
            <span class="theme-icon" id="themeIcon">🌙</span>
          </button>
          ${user ? `
            <div class="nav-user" id="navUser">
              <button class="nav-user-btn" id="navUserBtn">
                <span class="nav-avatar">${user.avatar || user.name.charAt(0).toUpperCase()}</span>
                <span class="nav-username">${user.name.split(' ')[0]}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
              </button>
              <div class="nav-dropdown" id="navDropdown">
                <div class="nav-dropdown-header">
                  <span class="nav-dropdown-name">${user.name}</span>
                  <span class="nav-dropdown-email">${user.email}</span>
                </div>
                <div class="nav-dropdown-divider"></div>
                <button class="nav-dropdown-item" id="logoutBtn">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                  <span>Logout</span>
                </button>
              </div>
            </div>
          ` : `
            <a href="/login/" class="btn btn-primary btn-sm nav-login-btn">Login</a>
          `}
          <button class="hamburger" id="hamburger" aria-label="Toggle menu">
            <span></span><span></span><span></span>
          </button>
        </div>
      </div>
    </nav>`;

    document.body.insertAdjacentHTML('afterbegin', navHTML);
    this._bindEvents();
  },

  _bindEvents() {
    // Hamburger
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    if (hamburger) {
      hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
      });
      navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
          hamburger.classList.remove('active');
          navLinks.classList.remove('active');
        });
      });
    }

    // User dropdown
    const userBtn = document.getElementById('navUserBtn');
    const dropdown = document.getElementById('navDropdown');
    if (userBtn && dropdown) {
      userBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
      });
      document.addEventListener('click', () => dropdown.classList.remove('show'));
    }

    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => Auth.logout());
    }

    // Scroll effect
    window.addEventListener('scroll', () => {
      const navbar = document.getElementById('navbar');
      if (navbar) {
        navbar.style.borderBottomColor = window.scrollY > 40
          ? 'var(--border-color-hover)'
          : 'var(--border-color)';
      }
    });
  }
};


// ==========================================
// MODULE: Theme – dark/light mode
// ==========================================
const Theme = {
  init() {
    const saved = localStorage.getItem('smartcampus-theme');
    if (saved) {
      document.documentElement.setAttribute('data-theme', saved);
    }
    this.updateIcon();
    // Bind after navbar is injected
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => this.toggle());
  },

  toggle() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('smartcampus-theme', next);
    this.updateIcon();
  },

  updateIcon() {
    const theme = document.documentElement.getAttribute('data-theme');
    const icon = document.getElementById('themeIcon');
    if (icon) icon.textContent = theme === 'dark' ? '🌙' : '☀️';
  }
};


// ==========================================
// MODULE: Toast Notifications
// ==========================================
const Toast = {
  _ensureContainer() {
    if (!document.getElementById('toastContainer')) {
      document.body.insertAdjacentHTML('beforeend', '<div class="toast-container" id="toastContainer"></div>');
    }
  },

  show(message, icon = '✅') {
    this._ensureContainer();
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 3200);
  }
};


// ==========================================
// MODULE: Loading Spinner
// ==========================================
const Loader = {
  _ensureOverlay() {
    if (!document.getElementById('loadingOverlay')) {
      document.body.insertAdjacentHTML('beforeend', `
        <div class="loading-overlay" id="loadingOverlay">
          <div class="spinner-container">
            <div class="spinner"></div>
            <p class="spinner-text">Finding the best matches for you...</p>
          </div>
        </div>`);
    }
  },

  show() {
    this._ensureOverlay();
    document.getElementById('loadingOverlay').classList.add('active');
  },

  hide() {
    const el = document.getElementById('loadingOverlay');
    if (el) el.classList.remove('active');
  }
};


// ==========================================
// Shared init – call from every page
// ==========================================
function initShared() {
  Navbar.init();
  Theme.init();
  GooeyNav.init();
}
