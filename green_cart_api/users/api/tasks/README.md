# Welcome Email Tasks

This directory contains Celery tasks for sending automated emails to users.

## Tasks

### `send_welcome_email(user_id)`
Sends a professional welcome email to newly registered users after they verify their email address.

**Parameters:**
- `user_id` (int): The ID of the user to send the welcome email to

**Features:**
- Professional HTML email template with Green Cart branding
- Personalized greeting using user's first name
- Information about account features and benefits
- Eco-friendly messaging aligned with Green Cart's mission
- Automatic retry mechanism (max 3 retries with exponential backoff)
- Comprehensive logging for monitoring and debugging

**Email Template:** `templates/emails/welcome_email.html`

### `send_bulk_welcome_emails(user_ids)`
Sends welcome emails to multiple users in bulk.

**Parameters:**
- `user_ids` (list): List of user IDs to send welcome emails to

**Returns:**
- Dictionary with results for each user

### `send_email_verification_reminder(user_id)`
Sends a reminder email to users who haven't verified their email address.

**Parameters:**
- `user_id` (int): The ID of the user to send the reminder to

## Usage

### Automatic Triggering
Welcome emails are automatically sent when a user verifies their email address through the `/api/verify_email/` endpoint.

### Manual Triggering
You can manually trigger welcome emails using the management command:

```bash
# Send welcome email synchronously (for testing)
python manage.py test_welcome_email --user-id 1

# Send welcome email by email address
python manage.py test_welcome_email --email user@example.com

# Send welcome email asynchronously using Celery
python manage.py test_welcome_email --user-id 1 --async
```

### Programmatic Usage
```python
from green_cart_api.users.api.tasks.email_tasks import send_welcome_email

# Send asynchronously
task = send_welcome_email.delay(user_id)

# Send synchronously (for testing)
result = send_welcome_email(user_id)
```

## Email Template Features

The welcome email template includes:
- **Professional Design**: Clean, responsive HTML layout
- **Green Cart Branding**: Consistent with company colors and styling
- **Personalized Content**: Uses user's first name for personal touch
- **Feature Highlights**: Lists key account features and benefits
- **Call-to-Action**: Encourages users to explore the platform
- **Eco-Friendly Messaging**: Aligns with Green Cart's sustainable mission
- **Contact Information**: Provides support contact details

## Configuration

The email tasks use the existing `EmailUtil` class and Django email settings:
- SMTP configuration in `settings.py`
- Email templates in `templates/emails/`
- Celery configuration for task queuing and execution

## Monitoring

All tasks include comprehensive logging:
- Success/failure status
- User information
- Error details
- Retry attempts
- Task execution time

Check the application logs for email task execution details.

## Error Handling

- **User Not Found**: Task fails gracefully if user doesn't exist
- **Email Sending Failure**: Automatic retry with exponential backoff
- **Template Errors**: Comprehensive error logging
- **Network Issues**: Retry mechanism handles temporary failures

## Testing

Use the management command to test email functionality:
```bash
python manage.py test_welcome_email --user-id 1
```

This will send a test welcome email to the specified user.
