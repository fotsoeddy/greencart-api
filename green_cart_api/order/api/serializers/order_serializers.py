# green_cart_api/order/api/serializers/order_serializers.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from green_cart_api.order.models import Order, OrderItem
from green_cart_api.catalog.api.serializers.catalog_serializers import ProductListSerializer  # Assuming this exists for product details
from green_cart_api.users.api.serializers.user_serializer import UserSerializer  # Assuming a basic UserSerializer exists



class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    Handles individual order items with product details.
    """
    product = ProductListSerializer(read_only=True)  # Nested product info

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'quantity',
            'unit_price',
            'total_price',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'unit_price', 'total_price', 'created', 'modified']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be greater than zero."))
        return value


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    Handles the full order with nested items and calculated totals.
    """
    items = OrderItemSerializer(many=True, read_only=True)  # Nested items
    user = UserSerializer(read_only=True)  # Nested user info (optional, can be removed if not needed)
    items_count = serializers.ReadOnlyField()  # From model property

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'order_number',
            'status',
            'payment_status',
            'subtotal',
            'discount_amount',
            'tax_amount',
            'shipping_cost',
            'total',
            'shipping_address',
            'billing_address_same',
            'billing_address',
            'customer_note',
            'tracking_number',
            'shipping_method',
            'estimated_delivery',
            'paid_at',
            'shipped_at',
            'delivered_at',
            'items',
            'items_count',
            'created',
            'modified',
        ]
        read_only_fields = [
            'id', 'user', 'order_number', 'subtotal', 'total', 'items', 'items_count',
            'paid_at', 'shipped_at', 'delivered_at', 'created', 'modified',
        ]

    def create(self, validated_data):
        # Custom create logic if needed (e.g., from cart), but for now, basic
        order = Order.objects.create(**validated_data)
        # Assuming items are created separately or via a custom view
        return order

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add any custom representation if needed
        return representation
    
