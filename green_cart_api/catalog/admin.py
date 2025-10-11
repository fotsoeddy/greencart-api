from django.contrib import admin
from .models import Category, Brand, Tag, Product, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'display_order', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_featured', 'parent')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'slug', 'price', 'quantity', 'in_stock', 'is_featured', 'brand')
    search_fields = ('name', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_featured', 'is_bestseller', 'is_new', 'brand', 'categories')
    filter_horizontal = ('categories', 'tags')
    readonly_fields = ('discount_percentage', 'in_stock', 'is_low_stock')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'alt_text', 'is_primary', 'display_order')
    list_filter = ('is_primary',)
    search_fields = ('product__name', 'alt_text')