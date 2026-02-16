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

TEAM_SIZE_CHOICES = [

    ("just_me", "Just me"),
    ("2_5", "2–5 members"),
    ("5_10", "5–10 members"),
    ("10_25", "10–25 members"),
    ("25_plus", "25+ members"),

]

team_size = models.CharField(
    max_length=20,
    choices=TEAM_SIZE_CHOICES,
    default="just_me"
)


def __str__(self):
    return self.name