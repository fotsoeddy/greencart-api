import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from green_cart_api.users.models import GreenCartBaseModel
from green_cart_api.catalog.models import Product


class Wishlist(GreenCartBaseModel):
    """
    User wishlist model
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='wishlist',
        help_text=_("Wishlist owner")
    )
    name = models.CharField(
        max_length=255,
        default=_("My Wishlist"),
        help_text=_("Wishlist name")
    )
    is_public = models.BooleanField(
        default=False,
        help_text=_("Whether the wishlist is publicly visible")
    )

    class Meta:
        verbose_name = _("Wishlist")
        verbose_name_plural = _("Wishlists")
        ordering = ['-created']

    def __str__(self):
        return f"{self.user}'s Wishlist"

    @property
    def item_count(self):
        """Number of items in wishlist"""
        return self.items.count()

    def add_product(self, product):
        """Add product to wishlist"""
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=self,
            product=product
        )
        return wishlist_item

    def remove_product(self, product):
        """Remove product from wishlist"""
        self.items.filter(product=product).delete()

    def contains_product(self, product):
        """Check if product is in wishlist"""
        return self.items.filter(product=product).exists()

    def clear(self):
        """Clear all items from wishlist"""
        self.items.all().delete()


class WishlistItem(GreenCartBaseModel):
    """
    Individual items in wishlist
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items',
        help_text=_("Parent wishlist")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        help_text=_("Product in wishlist")
    )

    class Meta:
        verbose_name = _("Wishlist Item")
        verbose_name_plural = _("Wishlist Items")
        unique_together = ['wishlist', 'product']
        ordering = ['-created']

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user}'s wishlist"

    def move_to_cart(self, cart, quantity=1):
        """Move this item to shopping cart"""
        cart.add_item(self.product, quantity)
        self.delete()