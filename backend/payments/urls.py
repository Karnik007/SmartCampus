"""Payments API URL configuration."""

from django.urls import path
from . import views

app_name = 'payments_api'

urlpatterns = [
    path('create-order/', views.CreateOrderView.as_view(), name='create-order'),
    path('verify/', views.VerifyPaymentView.as_view(), name='verify-payment'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    path('orders/', views.OrderHistoryView.as_view(), name='order-history'),
]
