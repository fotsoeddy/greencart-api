import os

from celery import Celery
from celery.signals import setup_logging
from celery.schedules import crontab     

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("green_cart_api")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa: PLC0415

    from django.conf import settings  # noqa: PLC0415

    dictConfig(settings.LOGGING)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# In your Celery app configuration (e.g., celery_app.py)

        
app.conf.beat_schedule = {
    'send-pending-order-reminders-every-morning': {
        'task': 'green_cart_api.order.api.tasks.send_confirmation_email_tasks.check_and_send_pending_reminders',
        'schedule': crontab(hour=8, minute=0),  # Runs every day at 8:00 AM
    },
}