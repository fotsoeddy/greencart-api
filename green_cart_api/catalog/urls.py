from django.urls import path
from .api.views import (
    CategoryListView,
    CategoryDetailView,
    BrandListView,
    BrandDetailView,
    TagListView,
    TagDetailView,
    ProductListView,
    ProductDetailView,
    ProductImageListView,
    ProductImageDetailView,
)

app_name = 'catalog'

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),

    # Brands
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('brands/<slug:slug>/', BrandDetailView.as_view(), name='brand-detail'),

    # Tags
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('tags/<slug:slug>/', TagDetailView.as_view(), name='tag-detail'),

    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<slug:slug>/images/', ProductImageListView.as_view(), name='product-image-list'),
    path('products/<slug:slug>/images/<uuid:image_id>/', ProductImageDetailView.as_view(), name='product-image-detail'),
]


