import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from green_cart_api.users.models import GreenCartBaseModel
from green_cart_api.catalog.models import Product


class Cart(GreenCartBaseModel):
    """
    Shopping cart model for users
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='cart',
        help_text=_("Cart owner")
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        help_text=_("Session key for anonymous users")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether the cart is active")
    )

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")
        ordering = ['-created']

    def __str__(self):
        return f"Cart for {self.user.email if self.user else 'Anonymous'}"

    @property
    def item_count(self):
        """Total number of items in cart"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Total price of all items in cart"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_weight(self):
        """Total weight of all items in cart"""
        return sum(item.total_weight for item in self.items.all())

    def add_item(self, product, quantity=1):
        """Add product to cart or update quantity if already exists"""
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return cart_item

    def remove_item(self, product):
        """Remove product from cart"""
        self.items.filter(product=product).delete()

    def update_item_quantity(self, product, quantity):
        """Update quantity of a specific product in cart"""
        if quantity <= 0:
            self.remove_item(product)
        else:
            cart_item = self.items.filter(product=product).first()
            if cart_item:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                self.add_item(product, quantity)

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()

    def contains_product(self, product):
        """Check if product is in cart"""
        return self.items.filter(product=product).exists()

    def get_item(self, product):
        """Get cart item for specific product"""
        return self.items.filter(product=product).first()


class CartItem(GreenCartBaseModel):
    """
    Individual items in shopping cart
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        help_text=_("Parent cart")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        help_text=_("Product in cart")
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Quantity of product")
    )
    price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Price when added to cart")
    )

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        unique_together = ['cart', 'product']
        ordering = ['-created']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} in cart"

    def save(self, *args, **kwargs):
        # Store the current price when adding to cart
        if not self.price_at_time:
            self.price_at_time = self.product.price
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        """Total price for this cart item"""
        return self.price_at_time * self.quantity

    @property
    def total_weight(self):
        """Total weight for this cart item"""
        if self.product.weight:
            return self.product.weight * self.quantity
        return Decimal('0.00')

    @property
    def is_available(self):
        """Check if product is still available"""
        if not self.product.track_quantity:
            return True
        return self.product.quantity >= self.quantity

    @property
    def price_difference(self):
        """Price difference between cart price and current price"""
        return self.product.price - self.price_at_time

    def move_to_wishlist(self, wishlist):
        """Move this item to wishlist"""
        wishlist.add_product(self.product)
        self.delete()