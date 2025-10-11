# green_cart_api/users/management/commands/test_welcome_email.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from green_cart_api.users.api.tasks.email_tasks import send_welcome_email

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the welcome email functionality by sending a welcome email to a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to send welcome email to',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send welcome email to',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Send email asynchronously using Celery (default: synchronous)',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        email = options.get('email')
        use_async = options.get('async', False)

        # Find user by ID or email
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return
        elif email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {email} not found')
                )
                return
        else:
            self.stdout.write(
                self.style.ERROR('Please provide either --user-id or --email')
            )
            return

        self.stdout.write(f'Sending welcome email to user: {user.email} (ID: {user.id})')

        if use_async:
            # Send asynchronously using Celery
            try:
                task = send_welcome_email.delay(user.id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Welcome email task queued successfully! Task ID: {task.id}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to queue welcome email task: {str(e)}')
                )
        else:
            # Send synchronously for testing
            try:
                result = send_welcome_email(user.id)
                if result:
                    self.stdout.write(
                        self.style.SUCCESS('Welcome email sent successfully!')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Failed to send welcome email')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error sending welcome email: {str(e)}')
                )
