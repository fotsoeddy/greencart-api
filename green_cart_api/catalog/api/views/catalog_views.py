import logging
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from green_cart_api.catalog.models import Category, Brand, Tag, Product, ProductImage
from ..serializers import (
    CategorySerializer,
    BrandSerializer,
    TagSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
)

logger = logging.getLogger(__name__)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List categories",
        parameters=[
            OpenApiParameter(name='parent', description='Filter by parent id', required=False, type=int),
            OpenApiParameter(name='is_featured', description='Filter featured categories', required=False, type=bool),
        ],
        responses={200: CategorySerializer(many=True)},
    )
    def get(self, request):
        queryset = Category.objects.filter(is_active=True).order_by('display_order', 'name')
        parent = request.query_params.get('parent')
        if parent is not None:
            queryset = queryset.filter(parent_id=parent)
        is_featured = request.query_params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        data = CategorySerializer(queryset, many=True, context={'request': request}).data
        return Response(data)

    @extend_schema(
        summary="Create category",
        request=CategorySerializer,
        responses={201: CategorySerializer},
    )
    def post(self, request):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CategorySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Retrieve category", responses={200: CategorySerializer})
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug, is_active=True)
        return Response(CategorySerializer(category, context={'request': request}).data)

    @extend_schema(summary="Update category", request=CategorySerializer, responses={200: CategorySerializer})
    def patch(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        category = get_object_or_404(Category, slug=slug)
        serializer = CategorySerializer(category, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary="Delete category", responses={204: OpenApiResponse(description='Deleted')})
    def delete(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        category = get_object_or_404(Category, slug=slug)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BrandListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="List brands", responses={200: BrandSerializer(many=True)})
    def get(self, request):
        queryset = Brand.objects.filter(is_active=True).order_by('name')
        data = BrandSerializer(queryset, many=True, context={'request': request}).data
        return Response(data)

    @extend_schema(summary="Create brand", request=BrandSerializer, responses={201: BrandSerializer})
    def post(self, request):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = BrandSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BrandDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Retrieve brand", responses={200: BrandSerializer})
    def get(self, request, slug):
        brand = get_object_or_404(Brand, slug=slug, is_active=True)
        return Response(BrandSerializer(brand, context={'request': request}).data)

    @extend_schema(summary="Update brand", request=BrandSerializer, responses={200: BrandSerializer})
    def patch(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        brand = get_object_or_404(Brand, slug=slug)
        serializer = BrandSerializer(brand, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary="Delete brand", responses={204: OpenApiResponse(description='Deleted')})
    def delete(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        brand = get_object_or_404(Brand, slug=slug)
        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="List tags", responses={200: TagSerializer(many=True)})
    def get(self, request):
        queryset = Tag.objects.filter(is_active=True).order_by('name')
        data = TagSerializer(queryset, many=True, context={'request': request}).data
        return Response(data)

    @extend_schema(summary="Create tag", request=TagSerializer, responses={201: TagSerializer})
    def post(self, request):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = TagSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Retrieve tag", responses={200: TagSerializer})
    def get(self, request, slug):
        tag = get_object_or_404(Tag, slug=slug, is_active=True)
        return Response(TagSerializer(tag, context={'request': request}).data)

    @extend_schema(summary="Update tag", request=TagSerializer, responses={200: TagSerializer})
    def patch(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        tag = get_object_or_404(Tag, slug=slug)
        serializer = TagSerializer(tag, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary="Delete tag", responses={204: OpenApiResponse(description='Deleted')})
    def delete(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        tag = get_object_or_404(Tag, slug=slug)
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List products",
        parameters=[
            OpenApiParameter('q', str, OpenApiParameter.QUERY, description='Search query'),
            OpenApiParameter('category', str, OpenApiParameter.QUERY, description='Filter by category slug'),
            OpenApiParameter('brand', str, OpenApiParameter.QUERY, description='Filter by brand slug'),
            OpenApiParameter('tag', str, OpenApiParameter.QUERY, description='Filter by tag slug'),
            OpenApiParameter('min_price', str, OpenApiParameter.QUERY, description='Minimum price'),
            OpenApiParameter('max_price', str, OpenApiParameter.QUERY, description='Maximum price'),
            OpenApiParameter('is_featured', bool, OpenApiParameter.QUERY, description='Featured products'),
            OpenApiParameter('is_bestseller', bool, OpenApiParameter.QUERY, description='Bestsellers'),
            OpenApiParameter('is_new', bool, OpenApiParameter.QUERY, description='New products'),
            OpenApiParameter('in_stock', bool, OpenApiParameter.QUERY, description='Only in stock'),
            OpenApiParameter('ordering', str, OpenApiParameter.QUERY, description='Sort field'),
        ],
        responses={200: ProductListSerializer(many=True)},
    )
    def get(self, request):
        queryset = Product.objects.filter(is_active=True)

        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q))

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(categories__slug=category)

        brand = request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand__slug=brand)

        tag = request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        min_price = request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if request.query_params.get('is_featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        if request.query_params.get('is_bestseller') == 'true':
            queryset = queryset.filter(is_bestseller=True)
        if request.query_params.get('is_new') == 'true':
            queryset = queryset.filter(is_new=True)

        if request.query_params.get('in_stock') == 'true':
            queryset = queryset.filter(Q(track_quantity=False) | Q(quantity__gt=0))

        ordering = request.query_params.get('ordering')
        allowed_ordering = {'-created','created','-price','price','name','-name','-is_bestseller','is_bestseller'}
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created')

        data = ProductListSerializer(queryset.distinct(), many=True, context={'request': request}).data
        return Response(data)

    @extend_schema(summary="Create product", request=ProductDetailSerializer, responses={201: ProductDetailSerializer})
    def post(self, request):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductDetailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductDetailSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Retrieve product", responses={200: ProductDetailSerializer})
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        return Response(ProductDetailSerializer(product, context={'request': request}).data)

    @extend_schema(summary="Update product", request=ProductDetailSerializer, responses={200: ProductDetailSerializer})
    def patch(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, slug=slug)
        serializer = ProductDetailSerializer(product, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductDetailSerializer(product, context={'request': request}).data)

    @extend_schema(summary="Delete product", responses={204: OpenApiResponse(description='Deleted')})
    def delete(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, slug=slug)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductImageListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="List product images", responses={200: ProductImageSerializer(many=True)})
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        images = product.images.all().order_by('is_primary', 'display_order')
        return Response(ProductImageSerializer(images, many=True, context={'request': request}).data)

    @extend_schema(summary="Add product image", request=ProductImageSerializer, responses={201: ProductImageSerializer})
    def post(self, request, slug):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, slug=slug)
        serializer = ProductImageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductImageDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Update product image", request=ProductImageSerializer, responses={200: ProductImageSerializer})
    def patch(self, request, slug, image_id):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, slug=slug)
        image = get_object_or_404(ProductImage, id=image_id, product=product)
        serializer = ProductImageSerializer(image, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary="Delete product image", responses={204: OpenApiResponse(description='Deleted')})
    def delete(self, request, slug, image_id):
        if not IsAdminUser().has_permission(request, self):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, slug=slug)
        image = get_object_or_404(ProductImage, id=image_id, product=product)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


