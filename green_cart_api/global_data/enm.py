from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    PROCESSING = 'processing', _('Processing')
    SHIPPED = 'shipped', _('Shipped')
    DELIVERED = 'delivered', _('Delivered')
    CANCELLED = 'cancelled', _('Cancelled')
    REFUNDED = 'refunded', _('Refunded')


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    PAID = 'paid', _('Paid')
    FAILED = 'failed', _('Failed')
    REFUNDED = 'refunded', _('Refunded')


class DiscountType(models.TextChoices):
    PERCENTAGE = 'percentage', _('Percentage')
    FIXED_AMOUNT = 'fixed_amount', _('Fixed Amount')
    BUY_X_GET_Y = 'buy_x_get_y', _('Buy X Get Y')
    FREE_SHIPPING = 'free_shipping', _('Free Shipping')


class PromotionScope(models.TextChoices):
    ALL = 'all', _('All Products')
    PRODUCTS = 'products', _('Specific Products')
    CATEGORIES = 'categories', _('Product Categories')
    BRANDS = 'brands', _('Product Brands')


class ReviewStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')


class AddressType(models.TextChoices):  # 👈 new
    HOME = 'home', _('Home')
    WORK = 'work', _('Work')
    OTHER = 'other', _('Other')
