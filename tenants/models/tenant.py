import uuid
from django.db import models
from tenants.choices import TenantType , TeamSize , TenantMemberRole
from django.conf import settings
from django.utils.text import slugify



from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL



class Tenant(models.Model):
    '''this models make a workspace or tenant 
    which can have multiple users linked to
    it with different roles.'''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    tenant_type = models.CharField(
        max_length=20,
        choices=TenantType.choices
    )
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_tenants"
    )
    team_size = models.CharField(
        max_length=20,
        choices=TeamSize.choices,
        default=TeamSize.JUST_ME
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    '''this is simple word to string method
    to return name of tenant when we print it.'''
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name    


class TenantMember(models.Model):
    ''' this is helper model to
        link users to tenants 
        with specific roles.'''

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="members"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenant_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=TenantMemberRole.choices,
        default=TenantMemberRole.PROFESSIONAL
    )

    is_active = models.BooleanField(
        default=True
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_members"
    )

    class Meta:

        db_table = "tenant_members"

        unique_together = ("tenant", "user")

        ordering = ["-joined_at"]
        indexes = [
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"
