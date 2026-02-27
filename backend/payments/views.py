"""
SmartCampus AI – Payments Views
Razorpay integration: create order, verify payment, and payment history.
"""

import logging
import razorpay
from decimal import Decimal
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserProfile
from .models import Order, Payment
from .serializers import (
    CreateOrderSerializer, VerifyPaymentSerializer,
    OrderSerializer, PaymentSerializer,
)

logger = logging.getLogger(__name__)


def _get_razorpay_client():
    """Get Razorpay client instance."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CreateOrderView(APIView):
    """POST /api/payment/create-order/ – Create a Razorpay order."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data['items']
        notes = serializer.validated_data.get('notes', '')

        # Calculate total
        total = sum(float(item['price']) * int(item.get('quantity', 1)) for item in items)
        total_paise = int(total * 100)  # Razorpay expects amount in paise

        # Create order in DB
        order = Order.objects.create(
            user=request.user,
            items=items,
            total_amount=Decimal(str(total)),
            notes=notes,
        )

        # Create Razorpay order
        try:
            client = _get_razorpay_client()
            razorpay_order = client.order.create({
                'amount': total_paise,
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'notes': {
                    'user_email': request.user.email,
                    'order_id': str(order.id),
                },
            })
            order.razorpay_order_id = razorpay_order['id']
            order.save(update_fields=['razorpay_order_id'])

            logger.info(f"Razorpay order created: {razorpay_order['id']} for user {request.user.email}")

            return Response({
                'order_id': order.id,
                'razorpay_order_id': razorpay_order['id'],
                'amount': total_paise,
                'currency': 'INR',
                'key_id': settings.RAZORPAY_KEY_ID,
                'user': {
                    'name': request.user.full_name,
                    'email': request.user.email,
                },
                'items': items,
            })

        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            order.status = 'failed'
            order.save(update_fields=['status'])
            return Response(
                {'error': 'Payment gateway error. Please try again.', 'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )


class VerifyPaymentView(APIView):
    """POST /api/payment/verify/ – Verify Razorpay payment signature."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # Find the order
            order = Order.objects.get(
                razorpay_order_id=data['razorpay_order_id'],
                user=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify signature with Razorpay
        try:
            client = _get_razorpay_client()
            client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature'],
            })

            # Payment verified – mark as paid
            order.status = 'paid'
            order.save(update_fields=['status'])

            # Record payment
            payment = Payment.objects.create(
                order=order,
                razorpay_payment_id=data['razorpay_payment_id'],
                razorpay_signature=data['razorpay_signature'],
                amount=order.total_amount,
                status='success',
            )

            # Update user profile stats
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.total_orders += 1
            profile.total_spent += order.total_amount
            profile.save(update_fields=['total_orders', 'total_spent'])

            logger.info(f"Payment verified: {data['razorpay_payment_id']} for order #{order.id}")

            return Response({
                'success': True,
                'message': 'Payment verified successfully!',
                'order': OrderSerializer(order).data,
                'payment_id': payment.razorpay_payment_id,
            })

        except razorpay.errors.SignatureVerificationError:
            logger.warning(f"Payment signature verification failed for order #{order.id}")
            order.status = 'failed'
            order.save(update_fields=['status'])

            Payment.objects.create(
                order=order,
                razorpay_payment_id=data['razorpay_payment_id'],
                amount=order.total_amount,
                status='failed',
                error_code='SIGNATURE_MISMATCH',
                error_description='Payment signature verification failed.',
            )

            return Response(
                {'error': 'Payment verification failed. If amount was deducted, it will be refunded.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentHistoryView(generics.ListAPIView):
    """GET /api/payment/history/ – User's payment history."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            order__user=self.request.user
        ).select_related('order').order_by('-created_at')


class OrderHistoryView(generics.ListAPIView):
    """GET /api/payment/orders/ – User's order history."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# ============================================
# Template-based web views
# ============================================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def payment_view(request):
    """GET /payment/ – Payment page."""
    return render(request, 'payments/payment.html')
