# green_cart_api/review/api/views/review_view.py

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from green_cart_api.review.models import Review, ReviewHelpful, ReviewImage
from green_cart_api.review.api.serializers.review_serialisers import (
    ReviewSerializer, ReviewImageSerializer, ReviewHelpfulSerializer, ReviewApproveSerializer
)
from green_cart_api.global_data.enm import ReviewStatus

class ReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get('product')
        queryset = Review.objects.all()
        if product_id:
            queryset = queryset.filter(product_id=product_id, status=ReviewStatus.APPROVED)
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user) | queryset.filter(status=ReviewStatus.APPROVED)
        serializer = ReviewSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Review, pk=pk)

    def get(self, request, pk):
        review = self.get_object(pk)
        if not request.user.is_staff and review.user != request.user and review.status != ReviewStatus.APPROVED:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    def put(self, request, pk):
        review = self.get_object(pk)
        if review.user != request.user:
            return Response({"detail": "You do not have permission to edit this review."}, status=status.HTTP_403_FORBIDDEN)
        if review.status != ReviewStatus.PENDING:
            return Response({"detail": "Cannot edit approved or rejected reviews."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        review = self.get_object(pk)
        if review.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not have permission to delete this review."}, status=status.HTTP_403_FORBIDDEN)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewMarkHelpfulView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if ReviewHelpful.objects.filter(review=review, user=request.user).exists():
            return Response({"detail": "You have already marked this review as helpful."}, status=status.HTTP_400_BAD_REQUEST)
        ReviewHelpful.objects.create(review=review, user=request.user)
        review.mark_helpful()
        return Response({"detail": "Review marked as helpful."})

class ReviewApproveView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewApproveSerializer(review, data={'status': ReviewStatus.APPROVED})
        if serializer.is_valid():
            review.approve()
            return Response({"detail": "Review approved."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewRejectView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewApproveSerializer(review, data={'status': ReviewStatus.REJECTED})
        if serializer.is_valid():
            review.reject()
            return Response({"detail": "Review rejected."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewImageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ReviewImage.objects.filter(review__user=request.user)
        serializer = ReviewImageSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        review_id = request.data.get('review')
        review = get_object_or_404(Review, pk=review_id, user=request.user)
        serializer = ReviewImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(review=review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewImageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(ReviewImage, pk=pk, review__user=self.request.user)

    def get(self, request, pk):
        image = self.get_object(pk)
        serializer = ReviewImageSerializer(image)
        return Response(serializer.data)

    def put(self, request, pk):
        image = self.get_object(pk)
        serializer = ReviewImageSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        image = self.get_object(pk)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewHelpfulListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ReviewHelpful.objects.filter(user=request.user)
        serializer = ReviewHelpfulSerializer(queryset, many=True)
        return Response(serializer.data)