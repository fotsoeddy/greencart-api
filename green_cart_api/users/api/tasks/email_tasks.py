# green_cart_api/users/api/tasks/email_tasks.py

import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from green_cart_api.global_data.email import EmailUtil

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id):
    """
    Celery task to send a welcome email to a newly registered user.
    
    Args:
        user_id (int): The ID of the user to send the welcome email to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get the user
        user = User.objects.get(id=user_id)
        
        # Skip if user doesn't exist or is not active
        if not user or not user.is_active:
            logger.warning(f"User {user_id} not found or not active, skipping welcome email")
            return False
            
        # Prepare email context
        context = {
            'first_name': user.first_name or user.username,
            'site_name': 'Green Cart',
            'site_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://greencart.com'
        }
        
        # Initialize email utility
        email_util = EmailUtil(prod=not settings.DEBUG)
        
        # Send welcome email
        logger.info(f"Sending welcome email to user {user_id} ({user.email})")
        
        email_sent = email_util.send_email_with_template(
            template='emails/welcome_email.html',
            context=context,
            receivers=[user.email],
            subject=_('Welcome to Green Cart - Your Eco-Friendly Shopping Journey Begins!')
        )
        
        if email_sent:
            logger.info(f"Welcome email successfully sent to user {user_id} ({user.email})")
            return True
        else:
            logger.error(f"Failed to send welcome email to user {user_id} ({user.email})")
            return False
            
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist")
        return False
        
    except Exception as exc:
        logger.error(f"Error sending welcome email to user {user_id}: {str(exc)}")
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying welcome email task for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for welcome email task for user {user_id}")
            return False


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_welcome_emails(self, user_ids):
    """
    Celery task to send welcome emails to multiple users.
    
    Args:
        user_ids (list): List of user IDs to send welcome emails to
        
    Returns:
        dict: Results of email sending for each user
    """
    results = {}
    
    for user_id in user_ids:
        try:
            result = send_welcome_email.delay(user_id)
            results[user_id] = {
                'status': 'queued',
                'task_id': result.id
            }
        except Exception as exc:
            logger.error(f"Error queuing welcome email for user {user_id}: {str(exc)}")
            results[user_id] = {
                'status': 'failed',
                'error': str(exc)
            }
    
    return results


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_email_verification_reminder(self, user_id):
    """
    Celery task to send email verification reminder to users who haven't verified their email.
    
    Args:
        user_id (int): The ID of the user to send the reminder to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get the user
        user = User.objects.get(id=user_id)
        
        # Skip if user is already active (verified)
        if user.is_active:
            logger.info(f"User {user_id} is already verified, skipping reminder email")
            return False
            
        # Prepare email context
        context = {
            'first_name': user.first_name or user.username,
            'site_name': 'Green Cart',
            'verification_link': f"{settings.FRONTEND_URL}/verify-email?token={user.email_verification_token}" if hasattr(user, 'email_verification_token') else None
        }
        
        # Initialize email utility
        email_util = EmailUtil(prod=not settings.DEBUG)
        
        # Send reminder email
        logger.info(f"Sending email verification reminder to user {user_id} ({user.email})")
        
        email_sent = email_util.send_email_with_template(
            template='emails/verification_email.html',
            context=context,
            receivers=[user.email],
            subject=_('Complete Your Green Cart Registration - Verify Your Email')
        )
        
        if email_sent:
            logger.info(f"Email verification reminder successfully sent to user {user_id} ({user.email})")
            return True
        else:
            logger.error(f"Failed to send email verification reminder to user {user_id} ({user.email})")
            return False
            
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist")
        return False
        
    except Exception as exc:
        logger.error(f"Error sending email verification reminder to user {user_id}: {str(exc)}")
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying email verification reminder task for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for email verification reminder task for user {user_id}")
            return False
