from django.db import models


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "pending"
    CONFIRMED = "CONFIRMED", "confirmed"
    CANCELLED = "CANCELLED", "cancelled"