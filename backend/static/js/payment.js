/* ===================================================
   SmartCampus AI – Payment Page Logic
   Razorpay checkout integration with order management
   =================================================== */

document.addEventListener('DOMContentLoaded', async () => {
    // Note: Django's @login_required handles auth server-side
    initShared();

    const orderRaw = sessionStorage.getItem('smartcampus-order');
    const orderCard = document.querySelector('.payment-card');
    const payBtn = document.getElementById('payBtn');

    if (!orderRaw) {
        document.getElementById('orderItems').innerHTML = `
            <div class="empty-state">
                <p>No items in your order.</p>
                <a href="/results/" class="btn btn-primary btn-sm" style="margin-top:1rem;">Browse Recommendations</a>
            </div>
        `;
        loadOrderHistory();
        return;
    }

    const orderData = JSON.parse(orderRaw);
    renderOrderSummary(orderData);
    loadOrderHistory();

    // ---- Pay Button ----
    payBtn.addEventListener('click', async () => {
        payBtn.disabled = true;
        payBtn.textContent = 'Processing...';

        try {
            // Create order via backend
            const response = await SmartAPI.createOrder(orderData.items);
            openRazorpayCheckout(response, orderData);
        } catch (err) {
            // Fallback: simulate payment for demo
            console.warn('Backend unavailable, simulating payment flow:', err);
            simulatePayment(orderData);
        }
    });
});


function renderOrderSummary(orderData) {
    const container = document.getElementById('orderItems');
    const totalEl = document.getElementById('orderTotal');
    const payBtn = document.getElementById('payBtn');

    let total = 0;
    container.innerHTML = orderData.items.map(item => {
        const subtotal = item.price * (item.quantity || 1);
        total += subtotal;
        return `
            <div class="order-item">
                <div class="order-item-info">
                    <span class="order-item-emoji">${item.image || '🍽️'}</span>
                    <div>
                        <div class="order-item-name">${item.name}</div>
                        <div class="order-item-type">${item.type || 'food'}</div>
                    </div>
                </div>
                <div class="order-item-price">
                    <span>₹${item.price}</span>
                    <span class="order-item-qty">× ${item.quantity || 1}</span>
                </div>
            </div>
        `;
    }).join('');

    totalEl.textContent = `₹${total}`;
    payBtn.disabled = false;
    payBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
            <line x1="1" y1="10" x2="23" y2="10"></line>
        </svg>
        Pay ₹${total} with Razorpay
    `;
}


function openRazorpayCheckout(orderResponse, orderData) {
    const options = {
        key: orderResponse.key_id,
        amount: orderResponse.amount,
        currency: orderResponse.currency || 'INR',
        name: 'SmartCampus AI',
        description: `Order: ${orderData.items.map(i => i.name).join(', ')}`,
        order_id: orderResponse.razorpay_order_id,
        prefill: {
            name: orderResponse.user?.name || Auth.getUser()?.name || '',
            email: orderResponse.user?.email || Auth.getUser()?.email || '',
        },
        theme: {
            color: '#6366f1',
        },
        handler: async function (response) {
            // Payment successful – verify with backend
            try {
                const result = await SmartAPI.verifyPayment({
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature,
                });
                showPaymentSuccess(result, orderData);
            } catch (err) {
                showPaymentFailure('Verification failed. If charged, your amount will be refunded.');
            }
        },
        modal: {
            ondismiss: function () {
                const payBtn = document.getElementById('payBtn');
                payBtn.disabled = false;
                payBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                        <line x1="1" y1="10" x2="23" y2="10"></line>
                    </svg>
                    Retry Payment
                `;
                Toast.show('Payment cancelled.', '⚠️');
            },
        },
    };

    const rzp = new Razorpay(options);
    rzp.on('payment.failed', function (response) {
        showPaymentFailure(response.error?.description || 'Payment failed. Please try again.');
    });
    rzp.open();
}


function simulatePayment(orderData) {
    // Simulate a 2-second payment process for demo
    Loader.show();
    setTimeout(() => {
        Loader.hide();
        const total = orderData.items.reduce((sum, i) => sum + i.price * (i.quantity || 1), 0);
        showPaymentSuccess({
            success: true,
            message: 'Payment simulated successfully! (Backend offline – demo mode)',
            payment_id: 'pay_demo_' + Date.now(),
            order: {
                id: Math.floor(Math.random() * 10000),
                total_amount: total,
                status: 'paid',
                items: orderData.items,
            },
        }, orderData);
    }, 2000);
}


function showPaymentSuccess(result, orderData) {
    sessionStorage.removeItem('smartcampus-order');

    // Hide order card, show status
    document.querySelector('.payment-card').style.display = 'none';
    const statusDiv = document.getElementById('paymentStatus');
    statusDiv.style.display = 'block';

    document.getElementById('paymentStatusIcon').textContent = '✅';
    document.getElementById('paymentStatusTitle').textContent = 'Payment Successful!';
    document.getElementById('paymentStatusMessage').textContent = result.message || 'Your order has been placed.';

    // Show receipt
    const receiptDiv = document.getElementById('paymentReceipt');
    receiptDiv.style.display = 'block';
    const total = orderData.items.reduce((sum, i) => sum + i.price * (i.quantity || 1), 0);
    receiptDiv.innerHTML = `
        <div class="receipt-header">🧾 Payment Receipt</div>
        <div class="receipt-row"><span>Order ID</span><span>#${result.order?.id || '—'}</span></div>
        <div class="receipt-row"><span>Payment ID</span><span>${result.payment_id || '—'}</span></div>
        <div class="receipt-row"><span>Items</span><span>${orderData.items.map(i => i.name).join(', ')}</span></div>
        <div class="receipt-row receipt-total"><span>Total Paid</span><span>₹${total}</span></div>
        <div class="receipt-row"><span>Status</span><span class="status-paid">Paid ✓</span></div>
    `;

    Toast.show('Payment completed! 🎉', '✅');
    loadOrderHistory();
}


function showPaymentFailure(message) {
    document.querySelector('.payment-card').style.display = 'none';
    const statusDiv = document.getElementById('paymentStatus');
    statusDiv.style.display = 'block';

    document.getElementById('paymentStatusIcon').textContent = '❌';
    document.getElementById('paymentStatusTitle').textContent = 'Payment Failed';
    document.getElementById('paymentStatusMessage').textContent = message;

    Toast.show('Payment failed. Please try again.', '❌');
}


async function loadOrderHistory() {
    const container = document.getElementById('orderHistory');
    try {
        const orders = await SmartAPI.getOrderHistory();
        if (!orders.results || orders.results.length === 0) {
            container.innerHTML = '<p class="empty-state">No past orders yet.</p>';
            return;
        }
        container.innerHTML = orders.results.slice(0, 5).map(order => `
            <div class="order-history-item">
                <div class="order-history-info">
                    <span class="order-history-id">#${order.id}</span>
                    <span class="order-history-date">${new Date(order.created_at).toLocaleDateString()}</span>
                </div>
                <div class="order-history-details">
                    <span>${order.items.map(i => i.name).join(', ')}</span>
                </div>
                <div class="order-history-amount">
                    <span>₹${order.total_amount}</span>
                    <span class="order-status order-status-${order.status}">${order.status}</span>
                </div>
            </div>
        `).join('');
    } catch {
        container.innerHTML = '<p class="empty-state">No past orders yet.</p>';
    }
}
