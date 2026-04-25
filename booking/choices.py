from django.db import models


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "pending"
    CONFIRMED = "CONFIRMED", "confirmed"
    CANCELLED = "CANCELLED", "cancelled"

class weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"
