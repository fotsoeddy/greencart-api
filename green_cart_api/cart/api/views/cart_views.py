# green_cart_api/cart/api/views/cart_views.py

from rest_framework import viewsets, status  # DRF viewsets for handling API endpoints
from rest_framework.decorators import action  # Decorator for custom actions in viewsets
from rest_framework.response import Response  # For returning API responses
from rest_framework.permissions import IsAuthenticatedOrReadOnly  # Permission class for authenticated access
from django.utils.translation import gettext_lazy as _  # For translations
from green_cart_api.cart.models import Cart, CartItem  # Import models
from green_cart_api.cart.api.serializers.cart_serializers import CartSerializer, CartItemSerializer  # Import serializers
from green_cart_api.catalog.models import Product  # Import Product model for references

class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Cart operations.
    Provides endpoints for viewing, updating, and managing the shopping cart.
    Supports both authenticated users (one cart per user) and anonymous sessions.
    """
    serializer_class = CartSerializer  # Default serializer for the viewset
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allow read for all, write for authenticated

    def get_queryset(self):
        """
        Get the queryset based on user or session.
        For authenticated users, return their cart; for anonymous, use session key.
        """
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user, is_active=True)  # Active cart for authenticated user
        else:
            session_key = self.request.session.session_key  # Get session key for anonymous
            if not session_key:
                self.request.session.create()  # Create session if none exists
                session_key = self.request.session.session_key
            return Cart.objects.filter(session_key=session_key, is_active=True)  # Active cart for session

    def perform_create(self, serializer):
        """
        Handle creation of a new cart, associating with user or session.
        """
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)  # Save with user if authenticated
        else:
            session_key = self.request.session.session_key  # Ensure session exists
            if not session_key:
                self.request.session.create()
            serializer.save(session_key=self.request.session.session_key)  # Save with session key

    @action(detail=False, methods=['get'], url_path='my-cart')
    def get_my_cart(self, request):
        """
        Custom action to retrieve the current user's cart.
        Creates a new cart if none exists.
        """
        try:
            cart = self.get_queryset().first()  # Get the first (and only) active cart
            if not cart:
                if request.user.is_authenticated:
                    cart = Cart.objects.create(user=request.user)  # Create for user
                else:
                    session_key = request.session.session_key
                    if not session_key:
                        request.session.create()
                    cart = Cart.objects.create(session_key=request.session.session_key)  # Create for session
            serializer = self.get_serializer(cart)  # Serialize the cart
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        """
        Custom action to add an item to the cart.
        Expects 'product_id' and optional 'quantity' in request data.
        """
        cart = self.get_object()  # Get the cart instance
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))  # Default quantity to 1
        try:
            product = Product.objects.get(id=product_id)  # Fetch the product
            cart_item = cart.add_item(product, quantity)  # Use model method to add
            serializer = CartItemSerializer(cart_item)  # Serialize the new/updated item
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        """
        Custom action to remove an item from the cart.
        Expects 'product_id' in request data.
        """
        cart = self.get_object()  # Get the cart instance
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)  # Fetch the product
            cart.remove_item(product)  # Use model method to remove
            return Response({'message': _("Item removed successfully")}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update-quantity')
    def update_quantity(self, request, pk=None):
        """
        Custom action to update item quantity in the cart.
        Expects 'product_id' and 'quantity' in request data.
        """
        cart = self.get_object()  # Get the cart instance
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        try:
            product = Product.objects.get(id=product_id)  # Fetch the product
            cart.update_item_quantity(product, quantity)  # Use model method to update
            return Response({'message': _("Quantity updated successfully")}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='clear')
    def clear_cart(self, request, pk=None):
        """
        Custom action to clear all items from the cart.
        """
        cart = self.get_object()  # Get the cart instance
        cart.clear()  # Use model method to clear
        return Response({'message': _("Cart cleared successfully")}, status=status.HTTP_200_OK)