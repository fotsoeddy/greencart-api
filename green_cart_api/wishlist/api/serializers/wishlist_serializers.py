from rest_framework import serializers
from green_cart_api.wishlist.models import Wishlist, WishlistItem
from green_cart_api.catalog.models import Product
from green_cart_api.catalog.api.serializers import ProductListSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_slug = serializers.SlugField(write_only=True, required=False)
    product_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Product.objects.all(), required=False
    )

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_slug', 'product_id', 'created']
        read_only_fields = ['id', 'created', 'product']

    def validate(self, attrs):
        if not attrs.get('product_slug') and not attrs.get('product_id'):
            raise serializers.ValidationError('Either product_slug or product_id is required.')
        return attrs

    def create(self, validated_data):
        wishlist = self.context['wishlist']
        product = validated_data.get('product_id')
        if not product:
            slug = validated_data.get('product_slug')
            product = Product.objects.get(slug=slug, is_active=True)
        return wishlist.add_product(product)


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'name', 'is_public', 'item_count', 'items']
        read_only_fields = ['id', 'item_count', 'items']

