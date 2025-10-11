# green_cart_api/users/tests/test_email_tasks.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from unittest.mock import patch, MagicMock
from green_cart_api.users.api.tasks.email_tasks import (
    send_welcome_email,
    send_bulk_welcome_emails,
    send_email_verification_reminder
)

User = get_user_model()


class EmailTasksTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            username='johndoe'
        )
        self.user.is_active = True
        self.user.save()

    def test_send_welcome_email_success(self):
        """Test successful welcome email sending"""
        with patch('green_cart_api.users.api.tasks.email_tasks.EmailUtil') as mock_email_util:
            mock_instance = MagicMock()
            mock_instance.send_email_with_template.return_value = True
            mock_email_util.return_value = mock_instance
            
            result = send_welcome_email(self.user.id)
            
            self.assertTrue(result)
            mock_instance.send_email_with_template.assert_called_once()
            
            # Check the call arguments
            call_args = mock_instance.send_email_with_template.call_args
            self.assertEqual(call_args[1]['template'], 'emails/welcome_email.html')
            self.assertEqual(call_args[1]['receivers'], [self.user.email])
            self.assertIn('first_name', call_args[1]['context'])
            self.assertEqual(call_args[1]['context']['first_name'], 'John')

    def test_send_welcome_email_user_not_found(self):
        """Test welcome email with non-existent user"""
        result = send_welcome_email(99999)
        self.assertFalse(result)

    def test_send_welcome_email_inactive_user(self):
        """Test welcome email with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        result = send_welcome_email(self.user.id)
        self.assertFalse(result)

    def test_send_bulk_welcome_emails(self):
        """Test bulk welcome email sending"""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            first_name='Jane',
            username='janedoe'
        )
        user2.is_active = True
        user2.save()
        
        with patch('green_cart_api.users.api.tasks.email_tasks.send_welcome_email') as mock_task:
            mock_task.delay.return_value = MagicMock(id='task-123')
            
            result = send_bulk_welcome_emails([self.user.id, user2.id])
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[self.user.id]['status'], 'queued')
            self.assertEqual(result[user2.id]['status'], 'queued')

    def test_send_email_verification_reminder_active_user(self):
        """Test verification reminder with already active user"""
        result = send_email_verification_reminder(self.user.id)
        self.assertFalse(result)

    def test_send_email_verification_reminder_inactive_user(self):
        """Test verification reminder with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        with patch('green_cart_api.users.api.tasks.email_tasks.EmailUtil') as mock_email_util:
            mock_instance = MagicMock()
            mock_instance.send_email_with_template.return_value = True
            mock_email_util.return_value = mock_instance
            
            result = send_email_verification_reminder(self.user.id)
            
            self.assertTrue(result)
            mock_instance.send_email_with_template.assert_called_once()
            
            # Check the call arguments
            call_args = mock_instance.send_email_with_template.call_args
            self.assertEqual(call_args[1]['template'], 'emails/verification_email.html')
            self.assertEqual(call_args[1]['receivers'], [self.user.email])

    def test_welcome_email_template_context(self):
        """Test that welcome email template has correct context"""
        with patch('green_cart_api.users.api.tasks.email_tasks.EmailUtil') as mock_email_util:
            mock_instance = MagicMock()
            mock_instance.send_email_with_template.return_value = True
            mock_email_util.return_value = mock_instance
            
            send_welcome_email(self.user.id)
            
            call_args = mock_instance.send_email_with_template.call_args
            context = call_args[1]['context']
            
            # Check required context variables
            self.assertIn('first_name', context)
            self.assertIn('site_name', context)
            self.assertIn('site_url', context)
            
            # Check values
            self.assertEqual(context['first_name'], 'John')
            self.assertEqual(context['site_name'], 'Green Cart')
            self.assertIsNotNone(context['site_url'])
