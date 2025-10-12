# green_cart_api/order/api/tasks/send_confirmation_email_tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from green_cart_api.order.models import Order  # Adjust import if needed based on your project structure

@shared_task
def send_order_confirmation_email(order_id):
    """
    Send confirmation email when an order is created.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = 'Order Confirmation'
        message = f'Dear {order.user.username},\n\nYour order #{order.id} has been successfully created.\n\nDetails:\n- Status: {order.status}\n- Total: ${order.total}\n\nThank you for shopping with us!'
        send_mail(subject, message, 'no-reply@yourdomain.com', [order.user.email], fail_silently=False)
    except Order.DoesNotExist:
        pass  # Log error if needed

@shared_task
def send_order_cancellation_email(order_id):
    """
    Send email when an order is cancelled.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = 'Order Cancellation Notice'
        message = f'Dear {order.user.username},\n\nYour order #{order.id} has been cancelled.\n\nIf this was not intentional, please contact support.\n\nThank you.'
        send_mail(subject, message, 'no-reply@yourdomain.com', [order.user.email], fail_silently=False)
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
        subject = 'Order Update Notification'
        message = f'Dear {order.user.username},\n\nYour order #{order.id} has been updated.\n\nNew Status: {order.status}\nNew Total: ${order.total}\n\nPlease review your order details.'
        send_mail(subject, message, 'no-reply@yourdomain.com', [order.user.email], fail_silently=False)
    except Order.DoesNotExist:
        pass  # Log error if needed

@shared_task
def send_pending_order_reminder_email(order_id):
    """
    Send reminder email for a pending order.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = 'Pending Order Reminder'
        message = f'Dear {order.user.username},\n\nYour order #{order.id} is still pending and was created on {order.created.date()}.\n\nPlease complete your payment or contact support if needed.\n\nThank you.'
        send_mail(subject, message, 'no-reply@yourdomain.com', [order.user.email], fail_silently=False)
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