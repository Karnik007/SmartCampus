/* ===================================================
   SmartCampus AI – Trust Indicator Page Logic (v2)
   Uses SmartAPI for trust data, with local fallback
   =================================================== */

document.addEventListener('DOMContentLoaded', async () => {
    // Note: Django's @login_required handles auth server-side
    initShared();

    // Fetch trust data from backend or use defaults
    let trustData;
    try {
        trustData = await SmartAPI.getTrustScore();
    } catch {
        trustData = {
            overall: 92,
            budget_compliance: 100,
            preference_match: 90,
            explanation_clarity: 95,
            diversity_score: 82,
        };
    }

    // Update the ring meter value
    const ringText = document.querySelector('.trust-ring-value');
    if (ringText) ringText.textContent = `${trustData.overall}%`;

    // Update progress bars with real data
    const bars = document.querySelectorAll('.trust-bar-fill');
    const values = [
        trustData.budget_compliance,
        trustData.preference_match,
        trustData.explanation_clarity,
        trustData.diversity_score,
    ];

    bars.forEach((bar, idx) => {
        if (values[idx] !== undefined) {
            bar.style.setProperty('--bar-width', `${values[idx]}%`);
        }
    });

    // Animate after a short delay
    setTimeout(() => {
        const ring = document.getElementById('trustRingFill');
        if (ring) {
            const circumference = 2 * Math.PI * 54;
            const offset = circumference - (trustData.overall / 100) * circumference;
            ring.style.strokeDashoffset = offset;
            ring.classList.add('animated');
        }

        bars.forEach(bar => bar.classList.add('animated'));
    }, 400);
});
