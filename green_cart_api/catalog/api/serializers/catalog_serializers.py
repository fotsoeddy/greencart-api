from rest_framework import serializers
from green_cart_api.catalog.models import Category, Brand, Tag, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    has_children = serializers.BooleanField(read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'image',
            'display_order', 'is_featured', 'has_children', 'created', 
        ]
        read_only_fields = ['slug', 'created', ]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'website',
            'created'
        ]
        read_only_fields = ['slug', 'created']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'description', 'created', 
        ]
        read_only_fields = ['slug', 'created', ]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'display_order', 'created']
        read_only_fields = ['id', 'created']


class ProductListSerializer(serializers.ModelSerializer):
    brand = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    categories = serializers.SlugRelatedField(slug_field='slug', many=True, read_only=True)
    tags = serializers.SlugRelatedField(slug_field='slug', many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'price', 'compare_price',
            'discount_percentage', 'in_stock', 'is_featured', 'is_bestseller', 'is_new',
            'brand', 'categories', 'tags', 'created'
        ]
        read_only_fields = ['slug', 'created']


class ProductDetailSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    primary_image = ProductImageSerializer(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description', 'price', 'compare_price',
            'cost_price', 'quantity', 'low_stock_threshold', 'track_quantity', 'allow_backorders',
            'weight', 'dimensions', 'meta_title', 'meta_description', 'is_featured', 'is_bestseller',
            'is_new', 'brand', 'categories', 'tags', 'images', 'primary_image', 'in_stock',
            'is_low_stock', 'discount_percentage', 'created', 
        ]
        read_only_fields = ['slug', 'created', ]

