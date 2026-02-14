from django.db import models
from tenants.choices import TenantType
from django.contrib.auth import get_user_model


class Tenant(models.Model):

    name = models.CharField(max_length=255)

    tenant_type = models.CharField(
        max_length=20,
        choices=TenantType.CHOICES
    )
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)