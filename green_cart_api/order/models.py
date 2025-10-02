import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from green_cart_api.users.models import GreenCartBaseModel
from green_cart_api.catalog.models import Product


class Order(GreenCartBaseModel):
    """
    Order model for customer purchases
    """
    ORDER_STATUS_PENDING = 'pending'
    ORDER_STATUS_CONFIRMED = 'confirmed'
    ORDER_STATUS_PROCESSING = 'processing'
    ORDER_STATUS_SHIPPED = 'shipped'
    ORDER_STATUS_DELIVERED = 'delivered'
    ORDER_STATUS_CANCELLED = 'cancelled'
    ORDER_STATUS_REFUNDED = 'refunded'
    
    ORDER_STATUS_CHOICES = [
        (ORDER_STATUS_PENDING, _('Pending')),
        (ORDER_STATUS_CONFIRMED, _('Confirmed')),
        (ORDER_STATUS_PROCESSING, _('Processing')),
        (ORDER_STATUS_SHIPPED, _('Shipped')),
        (ORDER_STATUS_DELIVERED, _('Delivered')),
        (ORDER_STATUS_CANCELLED, _('Cancelled')),
        (ORDER_STATUS_REFUNDED, _('Refunded')),
    ]
    
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, _('Pending')),
        (PAYMENT_STATUS_PAID, _('Paid')),
        (PAYMENT_STATUS_FAILED, _('Failed')),
        (PAYMENT_STATUS_REFUNDED, _('Refunded')),
    ]
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='orders',
        help_text=_("User who placed the order")
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        help_text=_("Unique order identifier")
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=ORDER_STATUS_PENDING,
        help_text=_("Order status")
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING,
        help_text=_("Payment status")
    )
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Subtotal before discounts and tax")
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Total discount amount")
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Tax amount")
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Shipping cost")
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Final total amount")
    )
    
    # Customer information
    shipping_address = models.JSONField(
        help_text=_("Shipping address details")
    )
    billing_address = models.JSONField(
        help_text=_("Billing address details")
    )
    customer_note = models.TextField(
        blank=True,
        null=True,
        help_text=_("Customer notes or special instructions")
    )
    
    # Shipping information
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Shipping tracking number")
    )
    shipping_method = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Shipping method")
    )
    
    # Timestamps
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("When payment was completed")
    )
    shipped_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("When order was shipped")
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("When order was delivered")
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_paid(self):
        return self.payment_status == self.PAYMENT_STATUS_PAID

    @property
    def can_be_cancelled(self):
        return self.status in [self.ORDER_STATUS_PENDING, self.ORDER_STATUS_CONFIRMED]

    def calculate_totals(self):
        """Calculate order totals from items"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total = self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost
        self.save()


class OrderItem(GreenCartBaseModel):
    """
    Individual items in an order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text=_("Parent order")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        help_text=_("Product ordered")
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_("Quantity ordered")
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Price per unit at time of order")
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Total price for this line item")
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        ordering = ['created']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} - {self.order.order_number}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)