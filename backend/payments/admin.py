"""Payments Admin configuration."""

from django.contrib import admin
from .models import Order, Payment


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'currency', 'status', 'razorpay_order_id', 'created_at']
    list_filter = ['status', 'currency']
    search_fields = ['user__email', 'razorpay_order_id']
    readonly_fields = ['razorpay_order_id', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'razorpay_payment_id', 'amount', 'status', 'method', 'created_at']
    list_filter = ['status', 'method']
    search_fields = ['razorpay_payment_id', 'order__user__email']
    readonly_fields = ['created_at']
