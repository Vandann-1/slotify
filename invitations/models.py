import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Q, UniqueConstraint

from tenants.choices import TenantMemberRole
from .choices import InvitationStatus


class TenantInvitation(models.Model):
    # Tenant/workspace this invite belongs to
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    # Email being invited
    email = models.EmailField(db_index=True)

    # Role assigned after acceptance
    role = models.CharField(
        max_length=20,
        choices=TenantMemberRole.choices,
        default=TenantMemberRole.PROFESSIONAL,
    )

    # Invitation lifecycle state
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        db_index=True,
    )

    # Secure token used in invite link
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    # Who sent the invite
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            UniqueConstraint(
                fields=["tenant", "email"],
                condition=Q(status="pending"),
                name="unique_pending_invite_per_tenant_email",
            )
        ]

        indexes = [
            models.Index(fields=["email", "status"]),
        ]

    def __str__(self):
        return f"{self.email} → {self.tenant} ({self.status})"

    # Expiry helper
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    # Acceptance guard
    def can_accept(self):
        return (
            self.status == InvitationStatus.PENDING
            and not self.is_expired()
        )

    # Auto set expiry when created
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)