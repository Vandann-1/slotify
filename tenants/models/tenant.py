import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings

from tenants.choices import TemplateType, TeamSize, TenantMemberRole

User = settings.AUTH_USER_MODEL


class Tenant(models.Model):
    """
    Workspace (Tenant)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    #  CORE FIELD (controls system behavior)
    template_type = models.CharField(
        max_length=20,
        choices=TemplateType.choices,default=TemplateType.MENTOR,)

    # Optional (UI purpose)
    team_size = models.CharField(
        max_length=20,
        choices=TeamSize.choices,
        default=TeamSize.JUST_ME,
    )

    slug = models.SlugField(max_length=255, blank=True, unique=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_tenants",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------------
    # SLUG GENERATION
    # ---------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    # ---------------------------
    # HELPERS (NO NEED FOR SOLO/TEAM FIELD)
    # ---------------------------
    @property
    def is_team(self):
        return self.members.filter(is_active=True).count() > 1

    @property
    def is_solo(self):
        return not self.is_team

    def __str__(self):
        return self.name
    

class TenantMember(models.Model):
    """
    Links users to tenants with roles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=TenantMemberRole.choices,
        default=TenantMemberRole.PROFESSIONAL,
        db_index=True,
    )

    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_members",
    )

    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tenant_members"
        ordering = ["-joined_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user"],
                condition=models.Q(removed_at__isnull=True),
                name="unique_active_tenant_user",
            )
        ]

        indexes = [
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.tenant} ({self.role})"
    


