import uuid
from django.db import models # type: ignore
from django.utils.translation import gettext_lazy as _ # type: ignore
from django_extensions.db.models import TimeStampedModel, ActivatorModel # type: ignore
from django.utils.text import slugify # type: ignore
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class GreenCartBaseModel(TimeStampedModel, ActivatorModel):
    """
    Abstract base model for all GreenCart project models.

    Includes:
    - UUID primary key
    - Activation (is_active, activate(), deactivate())
    - Timestamp tracking (created, modified)
    - JSON metadata for extra context
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this instance."),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text=_("Optional extra metadata stored as JSON."),
    )

    class Meta:
        abstract = True
        ordering = ["-created"]



class User(AbstractBaseUser, PermissionsMixin, GreenCartBaseModel):
    first_name = models.CharField(max_length=100, help_text=_("User's first name."))
    last_name = models.CharField(max_length=100, help_text=_("User's last name."))
    email = models.EmailField(unique=True, help_text=_("Unique user email address."))
    is_admin = models.BooleanField(default=False, help_text=_("Designates whether the user is an admin."))
    is_active = models.BooleanField(default=True, help_text=_("Designates whether this user should be treated as active."))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin
