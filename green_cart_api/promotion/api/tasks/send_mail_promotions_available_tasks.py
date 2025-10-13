from celery import shared_task
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from green_cart_api.promotion.models import Promotion
from green_cart_api.users.models import User

logger = logging.getLogger(__name__)

# Hardcoded site details (move to settings.py in production)
SITE_NAME = 'Green Cart'
SITE_URL = 'https://www.greencart.com'
SUPPORT_EMAIL = 'support@greencart.com'

@shared_task
def send_new_promotion_emails(promotion_id):
    """
    Celery task to send emails to all active users notifying them of a new available promotion.
    This task is intended to be called asynchronously after creating or activating a new promotion.
    """
    try:
        promotion = Promotion.objects.prefetch_related('products', 'categories', 'brands').get(id=promotion_id)
        if not promotion.is_active or not promotion.is_valid:
            logger.info(f"Skipping promotion {promotion_id}: Active={promotion.is_active}, Valid={promotion.is_valid}")
            return

        # Get all active users with email addresses (assuming we send to customers)
        users = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')

        logger.info(f"Found {users.count()} active users for promotion {promotion_id}")

        # Prepare and send individual emails (for HTML support)
        subject = f"New Promotion Available: {promotion.name}"
        from_email = settings.EMAIL_HOST_USER

        for user in users:
            first_name = user.first_name or user.username
            plain_message = (
                f"Dear {first_name},\n\n"
                f"We're excited to announce a new promotion: {promotion.name}\n\n"
                f"Description: {promotion.description}\n"
                f"Discount: {promotion.discount_value} "
                f"{'%' if promotion.discount_type == 'percentage' else '$'} off\n"
                f"Valid from {promotion.start_date} to {promotion.end_date}\n"
                f"Coupon Code: {promotion.coupon_code if promotion.coupon_code else 'No code required'}\n\n"
                f"Shop now at Green Cart!\n\n"
                f"Best regards,\nGreen Cart Team"
            )
            html_message = render_to_string('emails/new_promotion_email.html', {
                'first_name': first_name,
                'promotion': promotion,
                'site_name': SITE_NAME,
                'site_url': SITE_URL,
                'support_email': SUPPORT_EMAIL,
            })
            send_mail(subject, plain_message, from_email, [user.email], html_message=html_message, fail_silently=False)

        logger.info(f"Sent {users.count()} emails for promotion {promotion_id}")

    except Promotion.DoesNotExist:
        logger.warning(f"Promotion {promotion_id} not found")
        pass
    except Exception as e:
        logger.error(f"Error sending promotion emails: {str(e)}")