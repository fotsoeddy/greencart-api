# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile, ShippingAddress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "is_admin", "is_active")
    list_filter = ("is_admin", "is_active")
    search_fields = ("email", "first_name", "last_name", "username")
    ordering = ("email",)
    readonly_fields = ("id", "last_login", "created", "modified")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Permissions"), {"fields": ("is_admin", "is_active", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "created", "modified")}),
        (_("Metadata"), {"fields": ("metadata",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "password1", "password2", "is_admin", "is_active"),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "date_of_birth", "gender", "phone_number", "newsletter_subscription")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone_number")
    list_filter = ("gender", "newsletter_subscription", "marketing_emails")
    readonly_fields = ("id", "created", "modified")
    autocomplete_fields = ("user",)


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "state", "postal_code", "country", "is_default", "is_active")
    list_filter = ("is_default", "is_active", "country")
    search_fields = ("user__email", "full_name", "address_line_1", "city", "state", "postal_code")
    readonly_fields = ("id", "created", "modified")
    autocomplete_fields = ("user",)
