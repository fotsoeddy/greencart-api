# green_cart_api/review/api/serializers/review_serialisers.py

from rest_framework import serializers
from green_cart_api.review.models import Review, ReviewImage, ReviewHelpful
from green_cart_api.global_data.enm import ReviewStatus

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'alt_text', 'created', 'modified']

class ReviewHelpfulSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewHelpful
        fields = ['id', 'review', 'user', 'created']

class ReviewSerializer(serializers.ModelSerializer):
    images = ReviewImageSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)  # Or use a custom serializer if needed

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'user', 'order', 'rating', 'title', 'comment',
            'status', 'is_verified_purchase', 'helpful_count', 'images',
            'created', 'modified'
        ]
        read_only_fields = ['user', 'status', 'is_verified_purchase', 'helpful_count']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        # Ensure user hasn't reviewed this product before
        user = self.context['request'].user
        product = data.get('product')
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ReviewApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['status']

    def validate_status(self, value):
        if value not in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            raise serializers.ValidationError("Invalid status for approval/rejection.")
        return value