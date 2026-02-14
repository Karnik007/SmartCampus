/* ===================================================
   SmartCampus AI – Dashboard Page Logic
   Form handling, slider live values, submit + redirect
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Note: Django's @login_required handles auth server-side

    // Init shared components (navbar, theme)
    initShared();

    // ---- Slider live values ----
    const budgetSlider = document.getElementById('budgetSlider');
    const budgetValue = document.getElementById('budgetValue');
    budgetSlider.addEventListener('input', () => {
        budgetValue.textContent = `₹${budgetSlider.value}`;
    });

    const weightSliders = [
        { input: 'weightPrice', output: 'weightPriceVal' },
        { input: 'weightRating', output: 'weightRatingVal' },
        { input: 'weightDistance', output: 'weightDistanceVal' }
    ];

    weightSliders.forEach(({ input, output }) => {
        const slider = document.getElementById(input);
        const display = document.getElementById(output);
        slider.addEventListener('input', () => {
            display.textContent = `${slider.value}%`;
        });
    });

    // ---- Restore previous preferences if any ----
    const saved = sessionStorage.getItem('smartcampus-prefs');
    if (saved) {
        try {
            const prefs = JSON.parse(saved);
            budgetSlider.value = prefs.budget;
            budgetValue.textContent = `₹${prefs.budget}`;
            document.getElementById('dietaryPref').value = prefs.dietary;
            document.getElementById('locationPref').value = prefs.location;
            document.getElementById('availableTime').value = prefs.availableTime;
            document.getElementById('weightPrice').value = prefs.weightPrice;
            document.getElementById('weightPriceVal').textContent = `${prefs.weightPrice}%`;
            document.getElementById('weightRating').value = prefs.weightRating;
            document.getElementById('weightRatingVal').textContent = `${prefs.weightRating}%`;
            document.getElementById('weightDistance').value = prefs.weightDistance;
            document.getElementById('weightDistanceVal').textContent = `${prefs.weightDistance}%`;

            // Restore checkboxes
            const boxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
            boxes.forEach(cb => {
                cb.checked = (prefs.interests || []).includes(cb.value);
            });
        } catch { /* ignore corrupt data */ }
    }

    // ---- Form submission ----
    document.getElementById('preferencesForm').addEventListener('submit', (e) => {
        e.preventDefault();

        const prefs = {
            budget: parseInt(budgetSlider.value),
            dietary: document.getElementById('dietaryPref').value,
            location: document.getElementById('locationPref').value,
            availableTime: parseInt(document.getElementById('availableTime').value),
            interests: Array.from(document.querySelectorAll('.checkbox-group input:checked')).map(cb => cb.value),
            weightPrice: parseInt(document.getElementById('weightPrice').value),
            weightRating: parseInt(document.getElementById('weightRating').value),
            weightDistance: parseInt(document.getElementById('weightDistance').value)
        };

        // Save to sessionStorage and navigate to results
        sessionStorage.setItem('smartcampus-prefs', JSON.stringify(prefs));
        window.location.href = '/results/';
    });
});
