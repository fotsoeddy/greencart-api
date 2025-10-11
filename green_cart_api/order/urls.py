# green_cart_api/order/urls.py

from django.urls import path
from .api.views.order_views import (
    OrderListView, OrderDetailView, OrderCreateView, OrderCancelView
)

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    # Add more paths for other actions if needed
]