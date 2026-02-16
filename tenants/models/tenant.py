from django.db import models
from tenants.choices import TenantType
from django.contrib.auth import get_user_model

User = get_user_model()


# User = get_user_model()

class Tenant(models.Model):

    name = models.CharField(max_length=255)

    tenant_type = models.CharField(
        max_length=20,
        choices=TenantType.CHOICES
    )

    email = models.EmailField(blank=True, null=True)

    phone = models.CharField(max_length=20, blank=True, null=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenants",
        null=True,
        blank=True
    )

created_at = models.DateTimeField(
    auto_now_add=True,
    null=True,
    blank=True
)

def __str__(self):
    return self.name