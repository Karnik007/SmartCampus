/* ===================================================
   SmartCampus AI – Gooey Nav Effect
   Vanilla JS port of ReactBits GooeyNav component.
   Adapted for multi-page Django app (delays navigation
   so particles can animate before the page changes).
   =================================================== */

const GooeyNav = {
    // Configuration
    animationTime: 600,
    particleCount: 15,
    particleDistances: [90, 10],
    particleR: 100,
    timeVariance: 300,
    colors: [1, 2, 3, 1, 2, 3, 1, 4],

    // DOM references
    container: null,
    navUl: null,
    filterEl: null,
    activeIndex: -1,
    _navigating: false,

    /**
     * Initialize the Gooey Nav effect on the navbar's nav-links <ul>.
     * Call AFTER the navbar has been injected into the DOM.
     */
    init() {
        const navUl = document.getElementById('navLinks');
        if (!navUl) return;

        this.navUl = navUl;

        // Wrap the <ul> in a gooey-nav-container
        const container = document.createElement('div');
        container.className = 'gooey-nav-container';
        navUl.parentNode.insertBefore(container, navUl);
        container.appendChild(navUl);
        this.container = container;

        // Create the filter effect overlay (gooey blur+contrast trick)
        this.filterEl = document.createElement('span');
        this.filterEl.className = 'gooey-effect gooey-filter';
        container.appendChild(this.filterEl);


        // Determine initial active index from current URL
        const items = navUl.querySelectorAll('li');
        items.forEach((li, i) => {
            const link = li.querySelector('a');
            if (link && link.classList.contains('active')) {
                this.activeIndex = i;
            }
            // Bind click on the <a> to intercept navigation
            if (link) {
                link.addEventListener('click', (e) => this._handleClick(e, i, link));
            }
        });

        // Position the pill on the active item (no particles on page load)
        if (this.activeIndex >= 0) {
            const activeLi = items[this.activeIndex];
            if (activeLi) {
                requestAnimationFrame(() => {
                    this._updateEffectPosition(activeLi);
                    this.filterEl.classList.add('active');
                });
            }
        }

        // Reposition on resize
        const resizeObserver = new ResizeObserver(() => {
            const items = this.navUl.querySelectorAll('li');
            if (this.activeIndex >= 0 && items[this.activeIndex]) {
                this._updateEffectPosition(items[this.activeIndex]);
            }
        });
        resizeObserver.observe(container);
    },

    // ---------- Private helpers ----------

    _noise(n) {
        n = n || 1;
        return n / 2 - Math.random() * n;
    },

    _getXY(distance, pointIndex, totalPoints) {
        const angle = ((360 + this._noise(8)) / totalPoints) * pointIndex * (Math.PI / 180);
        return [distance * Math.cos(angle), distance * Math.sin(angle)];
    },

    _createParticle(i, t, d, r) {
        let rotate = this._noise(r / 10);
        return {
            start: this._getXY(d[0], this.particleCount - i, this.particleCount),
            end: this._getXY(d[1] + this._noise(7), this.particleCount - i, this.particleCount),
            time: t,
            scale: 1 + this._noise(0.2),
            color: this.colors[Math.floor(Math.random() * this.colors.length)],
            rotate: rotate > 0 ? (rotate + r / 20) * 10 : (rotate - r / 20) * 10
        };
    },

    _makeParticles(element) {
        const d = this.particleDistances;
        const r = this.particleR;
        const bubbleTime = this.animationTime * 2 + this.timeVariance;
        element.style.setProperty('--gooey-time', `${bubbleTime}ms`);

        for (let i = 0; i < this.particleCount; i++) {
            const t = this.animationTime * 2 + this._noise(this.timeVariance * 2);
            const p = this._createParticle(i, t, d, r);
            element.classList.remove('active');

            setTimeout(() => {
                const particle = document.createElement('span');
                const point = document.createElement('span');
                particle.classList.add('gooey-particle');
                particle.style.setProperty('--start-x', `${p.start[0]}px`);
                particle.style.setProperty('--start-y', `${p.start[1]}px`);
                particle.style.setProperty('--end-x', `${p.end[0]}px`);
                particle.style.setProperty('--end-y', `${p.end[1]}px`);
                particle.style.setProperty('--gooey-time', `${p.time}ms`);
                particle.style.setProperty('--scale', `${p.scale}`);
                particle.style.setProperty('--color', `var(--gooey-color-${p.color}, white)`);
                particle.style.setProperty('--rotate', `${p.rotate}deg`);

                point.classList.add('gooey-point');
                particle.appendChild(point);
                element.appendChild(particle);

                requestAnimationFrame(() => {
                    element.classList.add('active');
                });

                setTimeout(() => {
                    try { element.removeChild(particle); } catch (e) { /* already removed */ }
                }, t);
            }, 30);
        }
    },

    _updateEffectPosition(element) {
        if (!this.container || !this.filterEl) return;

        const containerRect = this.container.getBoundingClientRect();
        const pos = element.getBoundingClientRect();

        // Fixed height, width relative to text
        const fixedHeight = 40;
        const hPadding = 16;
        const w = pos.width + hPadding;
        const centerX = (pos.x - containerRect.x) + pos.width / 2;
        const centerY = (pos.y - containerRect.y) + pos.height / 2;

        const styles = {
            left: `${centerX - w / 2}px`,
            top: `${centerY - fixedHeight / 2}px`,
            width: `${w}px`,
            height: `${fixedHeight}px`
        };

        Object.assign(this.filterEl.style, styles);
    },

    _handleClick(e, index, linkEl) {
        // Already on this page / already navigating
        if (this.activeIndex === index || this._navigating) return;

        // Prevent the default navigation so animation can play
        e.preventDefault();
        e.stopPropagation();
        this._navigating = true;

        const href = linkEl.getAttribute('href');
        const liEl = linkEl.parentElement;
        this.activeIndex = index;

        // Update active class on all links
        this.navUl.querySelectorAll('li a').forEach((a, i) => {
            a.classList.toggle('active', i === index);
        });

        // Position the effect over the clicked item
        this._updateEffectPosition(liEl);

        // Clear old particles
        this.filterEl.querySelectorAll('.gooey-particle').forEach(p => {
            try { this.filterEl.removeChild(p); } catch (e) { /* */ }
        });

        // Fire particles
        this._makeParticles(this.filterEl);

        // Navigate after a delay so the user sees the animation
        setTimeout(() => {
            if (href) window.location.href = href;
        }, 650);
    }
};
