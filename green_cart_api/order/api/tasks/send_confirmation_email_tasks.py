from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from green_cart_api.order.models import Order  # Adjust import if needed based on your project structure
from django.conf import settings  # Import for EMAIL_HOST_USER

# Hardcoded site details (move to settings.py in production)
SITE_NAME = 'Green Cart'
SITE_URL = 'https://www.greencart.com'
SUPPORT_EMAIL = 'support@greencart.com'

@shared_task
def send_order_confirmation_email(order_id):
    """
    Send confirmation email when an order is created.
    """
    try:
        order = Order.objects.get(id=order_id)
        first_name = order.user.first_name or order.user.username  # Fallback to username if first_name not available
        subject = 'Order Confirmation'
        plain_message = f'Dear {first_name},\n\nYour order #{order.id} has been successfully created.\n\nDetails:\n- Status: {order.status}\n- Total: ${order.total}\n\nThank you for shopping with us!'
        html_message = render_to_string('emails/order_email.html', {
            'first_name': first_name,
            'order': order,
            'site_name': SITE_NAME,
            'site_url': SITE_URL,
            'support_email': SUPPORT_EMAIL,
        })
        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [order.user.email], html_message=html_message, fail_silently=False)
    except Order.DoesNotExist:
        pass  # Log error if needed

@shared_task
def send_order_cancellation_email(order_id):
    """
    Send email when an order is cancelled.
    """
    try:
        order = Order.objects.get(id=order_id)
        first_name = order.user.first_name or order.user.username
        subject = 'Order Cancellation Notice'
        plain_message = f'Dear {first_name},\n\nYour order #{order.id} has been cancelled.\n\nIf this was not intentional, please contact support.\n\nThank you.'
        html_message = render_to_string('emails/order_cancellation.html', {
            'first_name': first_name,
            'order': order,
            'site_name': SITE_NAME,
            'site_url': SITE_URL,
            'support_email': SUPPORT_EMAIL,
        })
        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [order.user.email], html_message=html_message, fail_silently=False)
    except Order.DoesNotExist:
        pass  # Log error if needed

@shared_task
def send_order_update_email(order_id):
    """
    Send email when an order is modified (e.g., status or details changed).
    Note: This can be triggered via signals or views for updates.
    """
    try:
        order = Order.objects.get(id=order_id)
        first_name = order.user.first_name or order.user.username
        subject = 'Order Update Notification'
        plain_message = f'Dear {first_name},\n\nYour order #{order.id} has been updated.\n\nNew Status: {order.status}\nNew Total: ${order.total}\n\nPlease review your order details.'
        html_message = render_to_string('emails/order_update.html', {
            'first_name': first_name,
            'order': order,
            'site_name': SITE_NAME,
            'site_url': SITE_URL,
            'support_email': SUPPORT_EMAIL,
        })
        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [order.user.email], html_message=html_message, fail_silently=False)
    except Order.DoesNotExist:
        pass  # Log error if needed

@shared_task
def send_pending_order_reminder_email(order_id):
    """
    Send reminder email for a pending order.
    """
    try:
        order = Order.objects.get(id=order_id)
        first_name = order.user.first_name or order.user.username
        subject = 'Pending Order Reminder'
        plain_message = f'Dear {first_name},\n\nYour order #{order.id} is still pending and was created on {order.created.date()}.\n\nPlease complete your payment or contact support if needed.\n\nThank you.'
        html_message = render_to_string('emails/order_pending_reminder.html', {
            'first_name': first_name,
            'order': order,
            'site_name': SITE_NAME,
            'site_url': SITE_URL,
            'support_email': SUPPORT_EMAIL,
        })
        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [order.user.email], html_message=html_message, fail_silently=False)
    except Order.DoesNotExist:
        pass  # Log error if needed

@shared_task
def check_and_send_pending_reminders():
    """
    Periodic task to check for pending orders older than 1 day and send reminders.
    This should be scheduled to run every morning (e.g., via Celery Beat).
    """
    one_day_ago = timezone.now() - timedelta(days=1)
    pending_orders = Order.objects.filter(status='pending', created__lt=one_day_ago)
    for order in pending_orders:
        send_pending_order_reminder_email.delay(order.id)