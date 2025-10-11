# green_cart_api/order/api/views/order_views.py

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # Stricter for orders: authenticated only
from django.utils.translation import gettext_lazy as _
from green_cart_api.order.models import Order, OrderItem
from green_cart_api.order.api.serializers.order_serializers import OrderSerializer, OrderItemSerializer
from green_cart_api.catalog.models import Product  # For potential item creation
from decimal import Decimal

class OrderListView(APIView):
    """
    View to list all orders for the authenticated user.
    Method: GET
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderDetailView(GenericAPIView):
    """
    View to retrieve a specific order.
    Method: GET
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

class OrderCreateView(APIView):
    """
    View to create a new order.
    Method: POST
    Expects data like shipping_address, etc. Items might need to be added separately or from cart.
    For simplicity, assumes basic creation; customize for cart integration.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            # Temporarily set required fields to avoid not-null violation
            validated_data['subtotal'] = Decimal('0.00')
            validated_data['total'] = Decimal('0.00')
            order = Order.objects.create(**validated_data, user=request.user)
            # Example: Add items (customize as needed, e.g., from cart)
            # For now, assume items are passed in data as 'items': [{'product_id': 1, 'quantity': 2}, ...]
            items_data = request.data.get('items', [])
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity', 1)
                try:
                    product = Product.objects.get(id=product_id)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price  # Assume product has 'price'
                    )
                except Product.DoesNotExist:
                    return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
            order.calculate_totals()  # Recalculate and save
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Additional views if needed, e.g., for updating status (admin-only) or cancelling
class OrderCancelView(GenericAPIView):
    """
    View to cancel an order.
    Method: POST
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def post(self, request, pk=None):
        order = self.get_object()
        if not order.can_be_cancelled:
            return Response({'error': _("Order cannot be cancelled")}, status=status.HTTP_400_BAD_REQUEST)
        order.status = OrderStatus.CANCELLED
        order.save()
        return Response({'message': _("Order cancelled successfully")}, status=status.HTTP_200_OK)