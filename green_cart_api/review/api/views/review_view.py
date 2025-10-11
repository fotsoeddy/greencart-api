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
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

class ReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List reviews",
        description="Get reviews. Regular users see their own reviews and approved reviews. Staff see all reviews. Can filter by product.",
        parameters=[
            {'name': 'product', 'in': 'query', 'description': 'Filter by product ID', 'required': False, 'schema': {'type': 'integer'}}
        ],
        responses={
            200: OpenApiResponse(
                response=ReviewSerializer(many=True),
                description="List of reviews",
                examples=[
                    OpenApiExample(
                        "Reviews list",
                        summary="User's reviews and approved reviews",
                        description="Response showing reviews visible to the user",
                        value=[
                            {
                                "id": 1,
                                "user": 1,
                                "product": {
                                    "id": 1,
                                    "name": "iPhone 15",
                                    "slug": "iphone-15"
                                },
                                "rating": 5,
                                "title": "Excellent phone!",
                                "content": "This phone exceeded my expectations. Great camera, fast performance.",
                                "status": "approved",
                                "helpful_count": 12,
                                "is_helpful": False,
                                "images": [],
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
        product_id = request.query_params.get('product')
        queryset = Review.objects.all()
        if product_id:
            queryset = queryset.filter(product_id=product_id, status=ReviewStatus.APPROVED)
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user) | queryset.filter(status=ReviewStatus.APPROVED)
        serializer = ReviewSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create review",
        description="Create a new product review. Reviews are created with 'pending' status and require admin approval.",
        request=ReviewSerializer,
        responses={
            201: OpenApiResponse(
                response=ReviewSerializer,
                description="Review created successfully",
                examples=[
                    OpenApiExample(
                        "Create review request",
                        summary="Create new product review",
                        description="Request body for creating a new review",
                        value={
                            "product": 1,
                            "rating": 5,
                            "title": "Amazing product!",
                            "content": "This product is fantastic. Highly recommend it to everyone."
                        },
                        request_only=True,
                    ),
                    OpenApiExample(
                        "Review created response",
                        summary="Successfully created review",
                        description="Response after successful review creation",
                        value={
                            "id": 1,
                            "user": 1,
                            "product": {
                                "id": 1,
                                "name": "iPhone 15",
                                "slug": "iphone-15"
                            },
                            "rating": 5,
                            "title": "Amazing product!",
                            "content": "This product is fantastic. Highly recommend it to everyone.",
                            "status": "pending",
                            "helpful_count": 0,
                            "is_helpful": False,
                            "images": [],
                            "created": "2024-01-15T10:30:00Z",
                            "modified": "2024-01-15T10:30:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
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

    @extend_schema(
        summary="Get review details",
        description="Retrieve detailed information about a specific review.",
        responses={
            200: OpenApiResponse(
                response=ReviewSerializer,
                description="Review details",
                examples=[
                    OpenApiExample(
                        "Review details",
                        summary="Detailed review information",
                        description="Complete review information including product details",
                        value={
                            "id": 1,
                            "user": 1,
                            "product": {
                                "id": 1,
                                "name": "iPhone 15",
                                "slug": "iphone-15"
                            },
                            "rating": 5,
                            "title": "Excellent phone!",
                            "content": "This phone exceeded my expectations. Great camera, fast performance.",
                            "status": "approved",
                            "helpful_count": 12,
                            "is_helpful": False,
                            "images": [],
                            "created": "2024-01-15T10:30:00Z",
                            "modified": "2024-01-15T10:30:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(description="Review not found")
        }
    )
    def get(self, request, pk):
        review = self.get_object(pk)
        if not request.user.is_staff and review.user != request.user and review.status != ReviewStatus.APPROVED:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    @extend_schema(
        summary="Update review",
        description="Update a review. Only the review author can update their own reviews, and only if the review is still pending.",
        request=ReviewSerializer,
        responses={
            200: OpenApiResponse(
                response=ReviewSerializer,
                description="Review updated successfully"
            ),
            400: OpenApiResponse(description="Cannot edit approved/rejected reviews or invalid input"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Review not found")
        }
    )
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

    @extend_schema(
        summary="Delete review",
        description="Delete a review. Users can delete their own reviews, staff can delete any review.",
        responses={
            204: OpenApiResponse(description="Review deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Review not found")
        }
    )
    def delete(self, request, pk):
        review = self.get_object(pk)
        if review.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not have permission to delete this review."}, status=status.HTTP_403_FORBIDDEN)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewMarkHelpfulView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark review as helpful",
        description="Mark a review as helpful. Users can only mark each review as helpful once.",
        responses={
            200: OpenApiResponse(
                description="Review marked as helpful",
                examples=[
                    OpenApiExample(
                        "Review marked helpful",
                        summary="Successfully marked review as helpful",
                        description="Response when review is marked as helpful",
                        value={
                            "detail": "Review marked as helpful."
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Already marked as helpful",
                examples=[
                    OpenApiExample(
                        "Already helpful",
                        summary="Review already marked as helpful",
                        description="Response when review was already marked as helpful",
                        value={
                            "detail": "You have already marked this review as helpful."
                        },
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(description="Review not found")
        }
    )
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if ReviewHelpful.objects.filter(review=review, user=request.user).exists():
            return Response({"detail": "You have already marked this review as helpful."}, status=status.HTTP_400_BAD_REQUEST)
        ReviewHelpful.objects.create(review=review, user=request.user)
        review.mark_helpful()
        return Response({"detail": "Review marked as helpful."})

class ReviewApproveView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Approve review",
        description="Approve a pending review (admin only).",
        responses={
            200: OpenApiResponse(
                description="Review approved successfully",
                examples=[
                    OpenApiExample(
                        "Review approved",
                        summary="Successfully approved review",
                        description="Response when review is approved",
                        value={
                            "detail": "Review approved."
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data"),
            404: OpenApiResponse(description="Review not found")
        }
    )
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewApproveSerializer(review, data={'status': ReviewStatus.APPROVED})
        if serializer.is_valid():
            review.approve()
            return Response({"detail": "Review approved."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewRejectView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Reject review",
        description="Reject a pending review (admin only).",
        responses={
            200: OpenApiResponse(
                description="Review rejected successfully",
                examples=[
                    OpenApiExample(
                        "Review rejected",
                        summary="Successfully rejected review",
                        description="Response when review is rejected",
                        value={
                            "detail": "Review rejected."
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data"),
            404: OpenApiResponse(description="Review not found")
        }
    )
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