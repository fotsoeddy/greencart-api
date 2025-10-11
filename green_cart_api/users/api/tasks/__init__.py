# Import tasks to make them discoverable by Celery
from .email_tasks import (
    send_welcome_email,
    send_bulk_welcome_emails,
    send_email_verification_reminder,
)

__all__ = [
    'send_welcome_email',
    'send_bulk_welcome_emails', 
    'send_email_verification_reminder',
]
