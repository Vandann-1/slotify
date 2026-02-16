from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (
        "id",
        "username",
        "email",
        "full_name",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
    )

    ordering = ("id",)

    fieldsets = (

        (None, {"fields": ("username", "password")}),

        ("Personal Info", {"fields": ("full_name", "email")}),

        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser")}),

    )

    add_fieldsets = (

        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "full_name",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),

    )


admin.site.register(User, CustomUserAdmin)
