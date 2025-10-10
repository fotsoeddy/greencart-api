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

class PromotionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

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