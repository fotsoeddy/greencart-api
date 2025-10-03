# /home/eddy/projects/shella/green_cart/green_cart_api/green_cart_api/users/managers.py

import random
import string
import uuid
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def _generate_verification_token(self):
        """Generate a unique UUID token for email verification."""
        return str(uuid.uuid4())

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        # Remove explicit is_active from here; let extra_fields handle it
        extra_fields.setdefault("is_active", False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        verification_token = self._generate_verification_token()
        return user, verification_token

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_active", True)
        # Remove required fields for superuser prompt
        extra_fields.setdefault("first_name", "")
        extra_fields.setdefault("last_name", "")
        extra_fields.setdefault("username", email.split("@")[0])

        if extra_fields.get("is_admin") is not True:
            raise ValueError(_("Superuser must have is_admin=True."))

        user, _ = self.create_user(email, password, **extra_fields)
        return user
