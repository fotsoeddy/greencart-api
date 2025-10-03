import logging
import os
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, get_connection
from decouple import config  # If you're using python-decouple for env vars
from email.mime.image import MIMEImage


logger = logging.getLogger(__name__)


class EmailUtil:
    def __init__(self, prod: bool = True) -> None:
        """
        Email utility for sending plain or template-based emails.
        :param prod: Set False in dev/test environments to avoid real email sending.
        """
        self.prod = prod

    def _get_connection(self):
        """
        Create a secure SMTP connection using Gmail or custom SMTP credentials.
        """
        try:
            connection = get_connection(
                backend="django.core.mail.backends.smtp.EmailBackend",
                host="smtp.gmail.com",
                port=587,
                username=config("EMAIL_HOST_USER"),
                password=config("EMAIL_HOST_PASSWORD"),
                use_tls=True,
            )
            return connection
        except Exception as e:
            logger.error(f"Error creating email connection: {e}")
            return None

    def send_generic_email(
        self,
        subject: str,
        content: str,
        to: List[str],
        _from: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        inline_images: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send a generic HTML email with optional attachments.
        :param subject: Email subject
        :param content: Email body (HTML allowed)
        :param to: List of recipients
        :param _from: Custom from email (default: settings.EMAIL_HOST_USER)
        :param attachments: List of file paths to attach
        """
        logger.info("## Sending generic email ##")

        if not self.prod:
            subject = f"[TEST] {subject}"

        try:
            email_message = EmailMessage(
                subject=subject,
                body=content,
                from_email=_from or f"Green Cart <{config('EMAIL_HOST_USER')}>",
                to=to,
                connection=self._get_connection(),
            )
            email_message.content_subtype = "html"  # Ensure HTML emails

            # Attach files if any
            if attachments:
                for file_path in attachments:
                    try:
                        email_message.attach_file(file_path)
                        logger.info(f"Attached file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not attach file {file_path}: {e}")
                        
            # Inline images
            if inline_images:
                for cid, path in inline_images.items():
                    try:
                        with open(path, "rb") as img_file:
                            img = MIMEImage(img_file.read())
                            img.add_header("Content-ID", f"<{cid}>")
                            img.add_header("Content-Disposition", "inline", filename=os.path.basename(path))
                            email_message.attach(img)
                        logger.info(f"Inline image attached: {cid} -> {path}")
                    except Exception as e:
                        logger.warning(f"Could not attach inline image {path}: {e}")

            email_message.send(fail_silently=False)
            logger.info("Generic email sent successfully.")
            return True

        except Exception as e:
            logger.error(f"Exception while sending email: {e}")
            return False

    def send_email_with_template(
        self,
        template: str,
        context: Dict[str, Any],
        receivers: List[str],
        subject: str,
        attachments: Optional[List[str]] = None,
        inline_images: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send an email rendered from a Django template with optional attachments.
        :param template: Path to the template file
        :param context: Context dictionary for template rendering
        :param receivers: List of recipients
        :param subject: Email subject
        :param attachments: List of file paths to attach
        """
        try:
            context["subject"] = subject
            body = render_to_string(template_name=template, context=context)

            return self.send_generic_email(
                subject=subject,
                content=body,
                to=receivers,
                attachments=attachments,
                inline_images=inline_images
            )

        except Exception as e:
            logger.error(f"Error rendering/sending template email: {e}")
            return False
