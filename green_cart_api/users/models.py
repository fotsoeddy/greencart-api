import uuid
from django.db import models # type: ignore
from django.utils.translation import gettext_lazy as _ # type: ignore
from django_extensions.db.models import TimeStampedModel, ActivatorModel # type: ignore
from django.utils.text import slugify # type: ignore
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from green_cart_api.global_data.enm import AddressType
from .managers import UserManager
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


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




# Add this after your existing User model
class Profile(GreenCartBaseModel):
    """
    User profile model for additional user information
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text=_("User associated with this profile")
    )
    
    # Personal Information
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text=_("User's date of birth")
    )
    gender = models.CharField(
        max_length=25,
        choices=[
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
            ('prefer_not_to_say', _('Prefer not to say'))
        ],
        blank=True,
        null=True,
        help_text=_("User's gender")
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        help_text=_("User's phone number")
    )
    
    # Avatar/Profile Picture
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_("User's profile picture")
    )
    
    # Communication Preferences
    newsletter_subscription = models.BooleanField(
        default=True,
        help_text=_("Whether the user is subscribed to newsletter")
    )
    marketing_emails = models.BooleanField(
        default=True,
        help_text=_("Whether the user accepts marketing emails")
    )
    
    # Additional Metadata
    bio = models.TextField(
        blank=True,
        null=True,
        help_text=_("User's biography")
    )
    website = models.URLField(
        blank=True,
        null=True,
        help_text=_("User's website")
    )

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
        ordering = ['-created']

    def __str__(self):
        return f"Profile of {self.user}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def age(self):
        """Calculate user's age from date of birth"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    



class ShippingAddress(GreenCartBaseModel):
    """
    Shipping address model for storing user's shipping addresses
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shipping_addresses',
        help_text=_("User who owns this address")
    )

    # Address Type
    address_type = models.CharField(
        max_length=10,
        choices=AddressType.choices,  # 👈 use centralized choices
        default=AddressType.HOME,
        help_text=_("Type of address")
    )

    # Contact Information
    full_name = models.CharField(max_length=255, help_text=_("Full name for shipping"))
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text=_("Phone number for shipping")
    )

    # Address Details
    address_line_1 = models.CharField(max_length=255, help_text=_("Address line 1 (street address, P.O. box)"))
    address_line_2 = models.CharField(max_length=255, blank=True, null=True, help_text=_("Address line 2"))
    city = models.CharField(max_length=100, help_text=_("City"))
    state = models.CharField(max_length=100, help_text=_("State/Province/Region"))
    postal_code = models.CharField(max_length=20, help_text=_("Postal code"))
    country = models.CharField(max_length=100, default="United States", help_text=_("Country"))

    # Address Status
    is_default = models.BooleanField(default=False, help_text=_("Whether this is the default shipping address"))
    is_active = models.BooleanField(default=True, help_text=_("Whether this address is active"))

    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")
        ordering = ['-is_default', '-created']
        unique_together = ['user', 'address_line_1', 'postal_code']

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country
        ]
        return ", ".join(part for part in address_parts if part)

    def to_dict(self):
        return {
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'address_line_1': self.address_line_1,
            'address_line_2': self.address_line_2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'address_type': self.address_type
        }