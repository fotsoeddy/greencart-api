# green_cart_api/wishlist/api/tasks/wishlist_notifications_tasks.py

from celery import shared_task
import logging
from django.core.mail import send_mass_mail
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver  # Not needed if connecting directly
from green_cart_api.catalog.models import Product
from green_cart_api.wishlist.models import WishlistItem
from green_cart_api.users.models import User
from decimal import Decimal

logger = logging.getLogger(__name__)

# Signal to capture old values before save
def capture_old_values(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_price = old_instance.price
        instance._old_compare_price = old_instance.compare_price if hasattr(old_instance, 'compare_price') else None
    else:
        instance._old_price = None
        instance._old_compare_price = None

pre_save.connect(capture_old_values, sender=Product)

# Signal to check for price drop or sale after save
def check_for_notifications(sender, instance, created, **kwargs):
    if created or not hasattr(instance, '_old_price'):
        return

    old_price = instance._old_price
    new_price = instance.price
    old_compare = instance._old_compare_price or Decimal('0')
    new_compare = instance.compare_price or Decimal('0')

    # Calculate old and new discount percentages (assuming similar to property)
    old_discount = ((old_compare - old_price) / old_compare * 100) if old_compare > 0 else Decimal('0')
    new_discount = ((new_compare - new_price) / new_compare * 100) if new_compare > 0 else Decimal('0')

    # Detect beneficial change: price dropped or discount increased
    price_dropped = new_price < old_price
    discount_increased = new_discount > old_discount

    if price_dropped or discount_increased:
        # Queue the Celery task with old values
        send_wishlist_notifications.delay(
            instance.id,
            str(old_price),
            str(old_discount.quantize(Decimal('0.01'))),
            str(old_compare)
        )

post_save.connect(check_for_notifications, sender=Product)

@shared_task
def send_wishlist_notifications(product_id, old_price_str, old_discount_str, old_compare_str):
    """
    Celery task to send email notifications to users who have this product in their wishlist
    when there's a price drop or it goes on sale.
    """
    try:
        product = Product.objects.get(id=product_id)
        old_price = Decimal(old_price_str)
        old_discount = Decimal(old_discount_str)
        old_compare = Decimal(old_compare_str)

        # Recalculate current discount (assuming no property, or use if exists)
        # If Product has discount_percentage property, use product.discount_percentage
        # Here, calculate for consistency
        new_discount = ((product.compare_price - product.price) / product.compare_price * 100) if product.compare_price else Decimal('0')

        wishlist_items = WishlistItem.objects.filter(product=product)
        if not wishlist_items.exists():
            logger.info(f"No wishlists for product {product_id}")
            return

        messages = []
        from_email = settings.DEFAULT_FROM_EMAIL or 'no-reply@greencart.com'
        subject = f"Price Alert: {product.name} is on Sale!"

        for item in wishlist_items:
            user = item.wishlist.user
            if not user.email:
                continue

            # Craft personalized message
            message = f"Dear {user.get_full_name() or 'Customer'},\n\n"
            message += f"Great news! The product '{product.name}' in your wishlist has updated pricing:\n\n"

            if product.price < old_price:
                message += f"- Price dropped from ${old_price} to ${product.price}!\n"
            if new_discount > old_discount:
                message += f"- Now on sale with {new_discount:.2f}% off (previously {old_discount:.2f}%)!\n"

            message += f"\nDescription: {product.short_description or ''}\n"
            message += f"Shop now at Green Cart!\n\n"
            message += f"Best regards,\nGreen Cart Team"

            messages.append((subject, message, from_email, [user.email]))

        if messages:
            send_mass_mail(messages, fail_silently=False)
            logger.info(f"Sent {len(messages)} wishlist notifications for product {product_id}")
        else:
            logger.info(f"No valid users to notify for product {product_id}")

    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found")
    except Exception as e:
        logger.error(f"Error sending wishlist notifications: {str(e)}")