"""Payments serializers."""

from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from .models import Order, Payment


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'items', 'total_amount', 'currency', 'status',
            'razorpay_order_id', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'razorpay_order_id', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    """Input for creating a new Razorpay order."""
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text='List of {id, name, type, price, quantity}',
    )
    notes = serializers.CharField(required=False, default='')

    def validate_items(self, items):
        total = Decimal('0')
        for item in items:
            if 'price' not in item or 'name' not in item:
                raise serializers.ValidationError('Each item must have "name" and "price".')

            try:
                price = Decimal(str(item['price']))
                qty = int(item.get('quantity', 1))
            except (InvalidOperation, ValueError, TypeError):
                raise serializers.ValidationError('Invalid price or quantity format.')

            if price < 0 or qty < 1:
                raise serializers.ValidationError('Invalid price or quantity.')
            total += price * qty
        return items


class VerifyPaymentSerializer(serializers.Serializer):
    """Input for verifying a Razorpay payment."""
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'razorpay_payment_id', 'amount',
            'currency', 'status', 'method', 'created_at',
        ]
