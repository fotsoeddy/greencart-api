# green_cart_api/cart/api/serializers/cart_serializers.py

from rest_framework import serializers  # Assuming Django Rest Framework is used for API serialization
from django.utils.translation import gettext_lazy as _  # For translations
from green_cart_api.cart.models import Cart, CartItem  # Import the models from the cart app
from green_cart_api.catalog.api.serializers.catalog_serializers import ProductListSerializer  # Correct import for ProductListSerializer from catalog serializers

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem model.
    This serializer handles the serialization and deserialization of individual cart items,
    including product details, quantity, and calculated totals.
    """
    product = ProductListSerializer(read_only=True)  # Nested serializer for product details using ProductListSerializer (read-only to prevent modification)
    total_price = serializers.ReadOnlyField()  # Read-only field for calculated total price
    total_weight = serializers.ReadOnlyField()  # Read-only field for calculated total weight
    is_available = serializers.ReadOnlyField()  # Read-only field for availability check
    price_difference = serializers.ReadOnlyField()  # Read-only field for price difference

    class Meta:
        model = CartItem  # Specifies the model this serializer is for
        fields = [
            'id',  # Unique identifier for the cart item
            'product',  # Nested product information
            'quantity',  # Quantity of the product in the cart
            'price_at_time',  # Price captured when added to cart
            'total_price',  # Calculated total price
            'total_weight',  # Calculated total weight
            'is_available',  # Availability status
            'price_difference',  # Difference between current and captured price
            'created',  # Timestamp when item was created
            'modified',  # Timestamp when item was last updated (changed from 'updated')
        ]
        read_only_fields = ['id', 'price_at_time', 'created', 'modified']  # Fields that cannot be modified via API (changed from 'updated')

    def validate_quantity(self, value):
        """
        Validate the quantity field to ensure it's positive and product has sufficient stock if tracked.
        """
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be greater than zero."))
        product = self.initial_data.get('product')
        if product and product.track_quantity and product.quantity < value:
            raise serializers.ValidationError(_("Insufficient stock for this product."))
        return value

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    This serializer handles the cart as a whole, including nested items, totals, and user/session info.
    """
    items = CartItemSerializer(many=True, read_only=True)  # Nested serializer for all items in the cart
    item_count = serializers.ReadOnlyField()  # Read-only field for total item count
    total_price = serializers.ReadOnlyField()  # Read-only field for total cart price
    total_weight = serializers.ReadOnlyField()  # Read-only field for total cart weight

    class Meta:
        model = Cart  # Specifies the model this serializer is for
        fields = [
            'id',  # Unique identifier for the cart
            'user',  # Associated user (if authenticated)
            'session_key',  # Session key for anonymous users
            'is_active',  # Active status of the cart
            'items',  # List of cart items
            'item_count',  # Total number of items
            'total_price',  # Total price of cart
            'total_weight',  # Total weight of cart
            'created',  # Timestamp when cart was created
            'modified',  # Timestamp when cart was last updated (changed from 'updated')
        ]
        read_only_fields = ['id', 'user', 'session_key', 'items', 'item_count', 'total_price', 'total_weight', 'created', 'modified']  # Fields that cannot be modified directly (changed from 'updated')

    def to_representation(self, instance):
        """
        Override to_representation to include dynamic data or custom logic if needed.
        """
        representation = super().to_representation(instance)
        # Optionally add custom fields or computations here
        return representation