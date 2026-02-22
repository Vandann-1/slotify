

# Register your models here.
from django.contrib import admin
from .models import TenantInvitation


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "tenant",
        "role",
        "status",
        "invited_by",
        "created_at",
    )
    search_fields = ("email",)
    list_filter = ("status", "role")