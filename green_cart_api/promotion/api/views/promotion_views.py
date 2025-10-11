# green_cart_api/promotion/api/views/promotion_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from green_cart_api.promotion.models import Promotion, PromotionUsage
from green_cart_api.promotion.api.serializers.promotion_serializers import PromotionSerializer, PromotionUsageSerializer
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q, F
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

class PromotionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List promotions",
        description="Get list of available promotions. Regular users see only active promotions, staff see all promotions.",
        responses={200: PromotionSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Active promotions response",
                summary="List of active promotions",
                description="Response showing available promotions for regular users",
                value=[
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Summer Sale 20% Off",
                        "description": "Get 20% off on all summer items",
                        "discount_type": "percentage",
                        "discount_value": "20.00",
                        "scope": "all",
                        "minimum_purchase_amount": "50.00",
                        "minimum_quantity": None,
                        "maximum_discount_amount": "100.00",
                        "usage_limit": 1000,
                        "usage_count": 45,
                        "start_date": "2024-01-01T00:00:00Z",
                        "end_date": "2024-12-31T23:59:59Z",
                        "coupon_code": "SUMMER20",
                        "is_active": True,
                        "products": [],
                        "categories": [],
                        "brands": [],
                        "is_valid": True,
                        "created": "2024-01-01T00:00:00Z",
                        "modified": "2024-01-15T10:30:00Z"
                    }
                ],
                response_only=True,
            )
        ]
    )
    def get(self, request):
        if request.user.is_staff:
            promotions = Promotion.objects.all()
        else:
            promotions = Promotion.objects.filter(
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).filter(Q(usage_limit__isnull=True) | Q(usage_count__lt=F('usage_limit')))
        
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create promotion",
        description="Create a new promotion (staff only). Supports different discount types and scopes.",
        request=PromotionSerializer,
        responses={
            201: PromotionSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Create percentage discount",
                summary="Create 15% off promotion",
                description="Create a percentage-based promotion for all products",
                value={
                    "name": "New Year Sale",
                    "description": "15% off all products for New Year",
                    "discount_type": "percentage",
                    "discount_value": "15.00",
                    "scope": "all",
                    "minimum_purchase_amount": "25.00",
                    "maximum_discount_amount": "50.00",
                    "usage_limit": 500,
                    "start_date": "2024-01-01T00:00:00Z",
                    "end_date": "2024-01-31T23:59:59Z",
                    "coupon_code": "NEWYEAR15",
                    "is_active": True
                },
                request_only=True,
            ),
            OpenApiExample(
                "Create product-specific promotion",
                summary="Create product-specific discount",
                description="Create a promotion for specific products",
                value={
                    "name": "Electronics Sale",
                    "description": "$20 off electronics",
                    "discount_type": "fixed_amount",
                    "discount_value": "20.00",
                    "scope": "products",
                    "minimum_purchase_amount": "100.00",
                    "usage_limit": 200,
                    "start_date": "2024-02-01T00:00:00Z",
                    "end_date": "2024-02-28T23:59:59Z",
                    "coupon_code": "ELECTRONICS20",
                    "is_active": True,
                    "products": ["550e8400-e29b-41d4-a716-446655440010", "550e8400-e29b-41d4-a716-446655440011"]
                },
                request_only=True,
            ),
        ]
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PromotionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PromotionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Promotion.objects.get(pk=pk)
        except Promotion.DoesNotExist:
            return None

    def get(self, request, pk):
        promotion = self.get_object(pk)
        if not promotion:
            return Response({'error': 'Promotion not found'}, status=status.HTTP_404_NOT_FOUND)

        # Non-admins ne peuvent voir que les promotions valides
        if not request.user.is_staff and not promotion.is_valid:
            return Response({'error': 'Promotion is not valid'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PromotionSerializer(promotion)
        return Response(serializer.data)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        promotion = self.get_object(pk)
        if not promotion:
            return Response({'error': 'Promotion not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PromotionSerializer(promotion, data=request.data, partial=True)
        if serializer.is_valid():
            updated_promotion = serializer.save()

            # ✅ Sécurisation pour éviter les erreurs de type None
            if updated_promotion.usage_count is None:
                updated_promotion.usage_count = 0
            if updated_promotion.usage_limit is not None and updated_promotion.usage_limit < 0:
                updated_promotion.usage_limit = None

            updated_promotion.save()
            return Response(PromotionSerializer(updated_promotion).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ PATCH autorisé (redirigé vers PUT)
    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        promotion = self.get_object(pk)
        if not promotion:
            return Response({'error': 'Promotion not found'}, status=status.HTTP_404_NOT_FOUND)

        promotion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplyPromotionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Apply promotion to order",
        description="Apply a promotion/discount to a specific order. This endpoint calculates the discount amount based on the promotion rules and order details.",
        request=PromotionUsageSerializer,
        responses={
            201: PromotionUsageSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Apply percentage discount",
                summary="Apply 20% discount promotion",
                description="Apply a percentage-based promotion to an order",
                value={
                    "promotion": "550e8400-e29b-41d4-a716-446655440000",
                    "user": "550e8400-e29b-41d4-a716-446655440001",
                    "order": 123
                },
                request_only=True,
            ),
            OpenApiExample(
                "Apply fixed amount discount",
                summary="Apply $10 off promotion",
                description="Apply a fixed amount discount promotion to an order",
                value={
                    "promotion": "550e8400-e29b-41d4-a716-446655440002",
                    "user": "550e8400-e29b-41d4-a716-446655440001",
                    "order": 124
                },
                request_only=True,
            ),
            OpenApiExample(
                "Successful response",
                summary="Promotion applied successfully",
                description="Response when promotion is successfully applied to the order",
                value={
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "promotion": "550e8400-e29b-41d4-a716-446655440000",
                    "user": "550e8400-e29b-41d4-a716-446655440001",
                    "order": 123,
                    "discount_amount": "15.50",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-15T10:30:00Z"
                },
                response_only=True,
            ),
            OpenApiExample(
                "Error - Promotion not applicable",
                summary="Promotion not applicable",
                description="Response when promotion cannot be applied (e.g., minimum requirements not met)",
                value={
                    "error": "Promotion not applicable"
                },
                response_only=True,
            ),
            OpenApiExample(
                "Error - Promotion already used",
                summary="Promotion already applied",
                description="Response when promotion has already been applied to this order",
                value={
                    "order": ["This promotion has already been applied to this order."]
                },
                response_only=True,
            ),
        ]
    )
    def post(self, request):
        serializer = PromotionUsageSerializer(data=request.data)
        if serializer.is_valid():
            promotion = serializer.validated_data['promotion']
            order = serializer.validated_data['order']
            user = serializer.validated_data['user']

            if user != request.user and not request.user.is_staff:
                return Response({'error': 'Cannot apply promotion for another user'}, status=status.HTTP_403_FORBIDDEN)

            cart_total = order.total
            quantity = order.items.count()

            discount_amount = promotion.calculate_discount(cart_total, quantity)
            if discount_amount <= 0:
                return Response({'error': 'Promotion not applicable'}, status=status.HTTP_400_BAD_REQUEST)

            promotion_usage = serializer.save(discount_amount=discount_amount)
            promotion.increment_usage()

            return Response(PromotionUsageSerializer(promotion_usage).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)