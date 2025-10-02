import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from green_cart_api.users.models import GreenCartBaseModel
from green_cart_api.global_data.enm import DiscountType, PromotionScope


class Promotion(GreenCartBaseModel):
    """
    Base promotion model for discounts and special offers
    """
    name = models.CharField(
        max_length=255,
        help_text=_("Promotion name")
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Promotion description")
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        help_text=_("Type of discount")
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Discount value (percentage or fixed amount)")
    )
    scope = models.CharField(
        max_length=20,
        choices=PromotionScope.choices,
        default=PromotionScope.ALL,
        help_text=_("Scope of the promotion")
    )
    minimum_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Minimum purchase amount to qualify")
    )
    minimum_quantity = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_("Minimum quantity to qualify")
    )
    maximum_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Maximum discount amount (for percentage discounts)")
    )
    usage_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_("Maximum number of times this promotion can be used")
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of times this promotion has been used")
    )
    start_date = models.DateTimeField(
        help_text=_("Promotion start date and time")
    )
    end_date = models.DateTimeField(
        help_text=_("Promotion end date and time")
    )
    coupon_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Coupon code for the promotion")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether the promotion is active")
    )
    
    # Relationships for scoped promotions
    products = models.ManyToManyField(
        'catalog.Product',
        related_name='promotions',
        blank=True,
        help_text=_("Products included in the promotion")
    )
    categories = models.ManyToManyField(
        'catalog.Category',
        related_name='promotions',
        blank=True,
        help_text=_("Categories included in the promotion")
    )
    brands = models.ManyToManyField(
        'catalog.Brand',
        related_name='promotions',
        blank=True,
        help_text=_("Brands included in the promotion")
    )

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ['-created']

    def __str__(self):
        return self.name

    @property
    def is_valid(self):
        """Check if promotion is currently valid"""
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and
                (self.usage_limit is None or self.usage_count < self.usage_limit))

    def calculate_discount(self, cart_total, quantity=1):
        """Calculate discount amount based on promotion rules"""
        if not self.is_valid:
            return Decimal('0.00')
        
        # Check minimum requirements
        if (self.minimum_purchase_amount and 
            cart_total < self.minimum_purchase_amount):
            return Decimal('0.00')
            
        if (self.minimum_quantity and 
            quantity < self.minimum_quantity):
            return Decimal('0.00')
        
        # Calculate discount
        if self.discount_type == DiscountType.PERCENTAGE:
            discount = (cart_total * self.discount_value) / 100
            if self.maximum_discount_amount:
                discount = min(discount, self.maximum_discount_amount)
        elif self.discount_type == DiscountType.FIXED_AMOUNT:
            discount = min(self.discount_value, cart_total)
        else:
            discount = Decimal('0.00')
            
        return discount

    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save()


class PromotionUsage(GreenCartBaseModel):
    """
    Track promotion usage by customers
    """
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name='usages',
        help_text=_("Promotion used")
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='promotion_usages',
        help_text=_("User who used the promotion")
    )
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='promotion_usages',
        help_text=_("Order where promotion was used")
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Discount amount applied")
    )

    class Meta:
        verbose_name = _("Promotion Usage")
        verbose_name_plural = _("Promotion Usages")
        unique_together = ['promotion', 'order']

    def __str__(self):
        return f"{self.promotion.name} - {self.user}"