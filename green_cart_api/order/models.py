import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from green_cart_api.global_data.enm import OrderStatus, PaymentStatus
from green_cart_api.users.models import GreenCartBaseModel


class Order(GreenCartBaseModel):
    """
    Order model for customer purchases
    """
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
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        help_text=_("Order status")
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
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
    
    # Address Information
    shipping_address = models.ForeignKey(
        'users.ShippingAddress',
        on_delete=models.PROTECT,
        related_name='orders',
        help_text=_("Shipping address for this order")
    )
    billing_address_same = models.BooleanField(
        default=True,
        help_text=_("Whether billing address is same as shipping address")
    )
    billing_address = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Billing address details (if different from shipping)")
    )
    
    # Customer information
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
    estimated_delivery = models.DateField(
        blank=True,
        null=True,
        help_text=_("Estimated delivery date")
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
        
        # Store shipping address as JSON for record keeping
        if self.shipping_address and not self.billing_address and self.billing_address_same:
            self.billing_address = self.shipping_address.to_dict()
            
        super().save(*args, **kwargs)

    @property
    def is_paid(self):
        return self.payment_status == PaymentStatus.PAID

    @property
    def can_be_cancelled(self):
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    @property
    def items_count(self):
        """Total number of items in order"""
        return sum(item.quantity for item in self.items.all())

    def calculate_totals(self):
        """Calculate order totals from items"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total = self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost
        self.save()

    def get_shipping_address_display(self):
        """Get formatted shipping address"""
        if self.shipping_address:
            return self.shipping_address.full_address
        return "No shipping address"

    def set_billing_address(self, address_data):
        """Set billing address from dictionary"""
        self.billing_address = address_data
        self.billing_address_same = False
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
        'catalog.Product',
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