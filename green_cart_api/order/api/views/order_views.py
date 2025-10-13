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
from ....global_data.enm import OrderStatus
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

# Import tasks for email sending
from green_cart_api.order.api.tasks.send_confirmation_email_tasks import (
    send_order_confirmation_email,
    send_order_cancellation_email,
    send_order_update_email
)

class OrderListView(APIView):
    """
    View to list all orders for the authenticated user.
    Method: GET
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List user orders",
        description="Get all orders for the authenticated user, ordered by creation date (newest first).",
        responses={
            200: OpenApiResponse(
                response=OrderSerializer(many=True),
                description="List of user orders",
                examples=[
                    OpenApiExample(
                        "User orders",
                        summary="User's order history",
                        description="Response showing user's order history",
                        value=[
                            {
                                "id": 1,
                                "user": 1,
                                "status": "confirmed",
                                "payment_status": "paid",
                                "subtotal": "199.98",
                                "tax_amount": "19.99",
                                "shipping_amount": "9.99",
                                "total": "229.96",
                                "shipping_address": {
                                    "street": "123 Main St",
                                    "city": "New York",
                                    "state": "NY",
                                    "zip_code": "10001",
                                    "country": "US"
                                },
                                "billing_address": {
                                    "street": "123 Main St",
                                    "city": "New York",
                                    "state": "NY",
                                    "zip_code": "10001",
                                    "country": "US"
                                },
                                "items": [
                                    {
                                        "id": 1,
                                        "product": {
                                            "id": 1,
                                            "name": "iPhone 15",
                                            "slug": "iphone-15",
                                            "price": "999.00"
                                        },
                                        "quantity": 1,
                                        "unit_price": "999.00",
                                        "total_price": "999.00"
                                    }
                                ],
                                "created": "2024-01-15T10:30:00Z",
                                "modified": "2024-01-15T10:30:00Z"
                            }
                        ],
                        response_only=True,
                    )
                ]
            )
        }
    )
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

    @extend_schema(
        summary="Get order details",
        description="Retrieve detailed information about a specific order.",
        responses={
            200: OpenApiResponse(
                response=OrderSerializer,
                description="Order details",
                examples=[
                    OpenApiExample(
                        "Order details",
                        summary="Detailed order information",
                        description="Complete order information including items and addresses",
                        value={
                            "id": 1,
                            "user": 1,
                            "status": "confirmed",
                            "payment_status": "paid",
                            "subtotal": "199.98",
                            "tax_amount": "19.99",
                            "shipping_amount": "9.99",
                            "total": "229.96",
                            "shipping_address": {
                                "street": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "zip_code": "10001",
                                "country": "US"
                            },
                            "billing_address": {
                                "street": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "zip_code": "10001",
                                "country": "US"
                            },
                            "items": [
                                {
                                    "id": 1,
                                    "product": {
                                        "id": 1,
                                        "name": "iPhone 15",
                                        "slug": "iphone-15",
                                        "price": "999.00"
                                    },
                                    "quantity": 1,
                                    "unit_price": "999.00",
                                    "total_price": "999.00"
                                }
                            ],
                            "created": "2024-01-15T10:30:00Z",
                            "modified": "2024-01-15T10:30:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(description="Order not found")
        }
    )
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

    @extend_schema(
        summary="Create new order",
        description="Create a new order with items. Items can be provided in the request or added from cart.",
        request=OrderSerializer,
        responses={
            201: OpenApiResponse(
                response=OrderSerializer,
                description="Order created successfully",
                examples=[
                    OpenApiExample(
                        "Create order request",
                        summary="Create order with items",
                        description="Request body for creating a new order",
                        value={
                            "shipping_address": {
                                "street": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "zip_code": "10001",
                                "country": "US"
                            },
                            "billing_address": {
                                "street": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "zip_code": "10001",
                                "country": "US"
                            },
                            "items": [
                                {
                                    "product_id": 1,
                                    "quantity": 2
                                },
                                {
                                    "product_id": 2,
                                    "quantity": 1
                                }
                            ]
                        },
                        request_only=True,
                    ),
                    OpenApiExample(
                        "Order created response",
                        summary="Successfully created order",
                        description="Response after successful order creation",
                        value={
                            "id": 1,
                            "user": 1,
                            "status": "pending",
                            "payment_status": "pending",
                            "subtotal": "199.98",
                            "tax_amount": "19.99",
                            "shipping_amount": "9.99",
                            "total": "229.96",
                            "shipping_address": {
                                "street": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "zip_code": "10001",
                                "country": "US"
                            },
                            "billing_address": {
                                "street": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "zip_code": "10001",
                                "country": "US"
                            },
                            "items": [
                                {
                                    "id": 1,
                                    "product": {
                                        "id": 1,
                                        "name": "iPhone 15",
                                        "slug": "iphone-15",
                                        "price": "999.00"
                                    },
                                    "quantity": 2,
                                    "unit_price": "999.00",
                                    "total_price": "1998.00"
                                }
                            ],
                            "created": "2024-01-15T10:30:00Z",
                            "modified": "2024-01-15T10:30:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data"),
            404: OpenApiResponse(description="Product not found")
        }
    )
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
            # Trigger confirmation email task
            send_order_confirmation_email.delay(order.id)
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

    @extend_schema(
        summary="Cancel order",
        description="Cancel a specific order if it can be cancelled (e.g., not already shipped).",
        responses={
            200: OpenApiResponse(
                description="Order cancelled successfully",
                examples=[
                    OpenApiExample(
                        "Order cancelled",
                        summary="Successful cancellation",
                        description="Response when order is successfully cancelled",
                        value={
                            "message": "Order cancelled successfully"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Order cannot be cancelled",
                examples=[
                    OpenApiExample(
                        "Cannot cancel",
                        summary="Order cannot be cancelled",
                        description="Response when order cannot be cancelled",
                        value={
                            "error": "Order cannot be cancelled"
                        },
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(description="Order not found")
        }
    )
    def post(self, request, pk=None):
        order = self.get_object()
        if not order.can_be_cancelled:
            return Response({'error': _("Order cannot be cancelled")}, status=status.HTTP_400_BAD_REQUEST)
        order.status = OrderStatus.CANCELLED
        order.save()
        # Trigger cancellation email task
        send_order_cancellation_email.delay(order.id)
        return Response({'message': _("Order cancelled successfully")}, status=status.HTTP_200_OK)

# Optional: Add this view if you need to handle order modifications (e.g., update shipping, add/remove items, change status)
class OrderUpdateView(GenericAPIView):
    """
    View to update an existing order.
    Method: PATCH
    Allows partial updates, e.g., change status, addresses, etc.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Or IsAdminUser for some fields

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Update order",
        description="Partially update an order (e.g., change address, status). Items updates might require separate endpoints.",
        request=OrderSerializer(partial=True),
        responses={
            200: OpenApiResponse(
                response=OrderSerializer,
                description="Order updated successfully"
            ),
            400: OpenApiResponse(description="Invalid input data"),
            404: OpenApiResponse(description="Order not found")
        }
    )
    def patch(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            order.calculate_totals()  # Recalculate if needed
            # Trigger update email task
            send_order_update_email.delay(order.id)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)