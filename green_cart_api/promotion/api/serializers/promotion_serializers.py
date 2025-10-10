# green_cart_api/promotion/api/serializers/promotion_serializers.py
from rest_framework import serializers
from green_cart_api.promotion.models import Promotion, PromotionUsage, DiscountType, PromotionScope
from green_cart_api.catalog.models import Product, Category, Brand
from green_cart_api.users.models import User
from green_cart_api.order.models import Order
from django.utils import timezone
from decimal import Decimal

class PromotionSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        many=True,
        required=False
    )
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False
    )
    brands = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        many=True,
        required=False
    )
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_value',
            'scope', 'minimum_purchase_amount', 'minimum_quantity',
            'maximum_discount_amount', 'usage_limit', 'usage_count',
            'start_date', 'end_date', 'coupon_code', 'is_active',
            'products', 'categories', 'brands', 'is_valid', 'created', 'modified'
        ]
        read_only_fields = ['usage_count', 'created', 'modified', 'is_valid']

    def validate(self, data):
        # Validate discount_type and discount_value
        discount_type = data.get('discount_type', getattr(self.instance, 'discount_type', None))
        discount_value = data.get('discount_value', getattr(self.instance, 'discount_value', None))
        
        if discount_type == DiscountType.PERCENTAGE and discount_value is not None and discount_value > 100:
            raise serializers.ValidationError({
                'discount_value': 'Percentage discount cannot exceed 100.'
            })

        # Validate start_date and end_date (using fallbacks for partial updates)
        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })

        # Validate scope-specific relationships
        scope = data.get('scope', getattr(self.instance, 'scope', None))

        if scope == PromotionScope.PRODUCTS:
            products = data.get('products')
            if products is not None:
                if not products:
                    raise serializers.ValidationError({
                        'products': 'At least one product is required for product-scoped promotion.'
                    })
            elif not self.instance or not self.instance.products.exists():
                raise serializers.ValidationError({
                    'products': 'At least one product is required for product-scoped promotion.'
                })

        elif scope == PromotionScope.CATEGORIES:
            categories = data.get('categories')
            if categories is not None:
                if not categories:
                    raise serializers.ValidationError({
                        'categories': 'At least one category is required for category-scoped promotion.'
                    })
            elif not self.instance or not self.instance.categories.exists():
                raise serializers.ValidationError({
                    'categories': 'At least one category is required for category-scoped promotion.'
                })

        elif scope == PromotionScope.BRANDS:
            brands = data.get('brands')
            if brands is not None:
                if not brands:
                    raise serializers.ValidationError({
                        'brands': 'At least one brand is required for brand-scoped promotion.'
                    })
            elif not self.instance or not self.instance.brands.exists():
                raise serializers.ValidationError({
                    'brands': 'At least one brand is required for brand-scoped promotion.'
                })

        return data

class PromotionUsageSerializer(serializers.ModelSerializer):
    promotion = serializers.PrimaryKeyRelatedField(queryset=Promotion.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta:
        model = PromotionUsage
        fields = ['id', 'promotion', 'user', 'order', 'discount_amount', 'created', 'modified']
        read_only_fields = ['discount_amount', 'created', 'modified']

    def validate(self, data):
        promotion = data.get('promotion')
        order = data.get('order')
        
        # Check if promotion is valid
        if not promotion.is_valid:
            raise serializers.ValidationError({
                'promotion': 'This promotion is not valid.'
            })

        # Check if promotion has already been used for this order
        if PromotionUsage.objects.filter(promotion=promotion, order=order).exists():
            raise serializers.ValidationError({
                'order': 'This promotion has already been applied to this order.'
            })

        return data