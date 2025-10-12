# green_cart_api/promotion/api/tasks/send_mail_promotions_available_tasks.py

from celery import shared_task

@shared_task
def send_new_promotion_emails(promotion_id):
    """
    Celery task to send emails to all active users notifying them of a new available promotion.
    This task is intended to be called asynchronously after creating or activating a new promotion.
    """
    # Move imports here to avoid loading before Django is ready
    from django.core.mail import send_mass_mail
    from django.conf import settings
    from green_cart_api.promotion.models import Promotion
    from green_cart_api.users.models import User

    try:
        promotion = Promotion.objects.get(id=promotion_id)
        if not promotion.is_active or not promotion.is_valid:
            # Skip if the promotion is not active or valid
            return

        # Get all active users with email addresses (assuming we send to customers)
        users = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')

        # Prepare email messages for mass sending
        messages = []
        subject = f"New Promotion Available: {promotion.name}"
        message = (
            f"Dear Customer,\n\n"
            f"We're excited to announce a new promotion: {promotion.name}\n\n"
            f"Description: {promotion.description}\n"
            f"Discount: {promotion.discount_value} "
            f"{'%' if promotion.discount_type == 'percentage' else '$'} off\n"
            f"Valid from {promotion.start_date} to {promotion.end_date}\n"
            f"Coupon Code: {promotion.coupon_code if promotion.coupon_code else 'No code required'}\n\n"
            f"Shop now at Green Cart!\n\n"
            f"Best regards,\nGreen Cart Team"
        )
        from_email = settings.DEFAULT_FROM_EMAIL or 'no-reply@greencart.com'

        for user in users:
            messages.append((subject, message, from_email, [user.email]))

        # Send mass emails for efficiency
        if messages:
            send_mass_mail(messages, fail_silently=False)

    except Promotion.DoesNotExist:
        # Handle case where promotion was deleted before task runs
        pass
    except Exception as e:
        # Log the error (assuming Celery handles logging, or add custom logging)
        print(f"Error sending promotion emails: {str(e)}")