from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    full_name = models.CharField(max_length=255)

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("client", "Client"),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="admin"
    )
    
    def __str__(self):
        return self.username