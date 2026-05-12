import uuid
from django.db import models
from django.conf import settings
from tenants.models import Tenant
from booking.choices import BookingStatus
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models, transaction
from django.conf import settings  # Import settings for the User model

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone





User = settings.AUTH_USER_MODEL
DAYS_OF_WEEK = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError


# 1. Service Model (Lives in booking app)
class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', # Keep string ref if Tenant is in another app
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration = models.IntegerField(help_text="In minutes (e.g., 30)")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

# 2. Availability Model (Lives in booking app)
class Availability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)   
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availabilities")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="availabilities")
    day_of_week = models.IntegerField(null=True, blank=True)
    date_specific = models.DateField(null=True, blank=True, help_text="Overrides day_of_week if set")
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    slot_duration = models.IntegerField(help_text="In minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

# 3. Booking Status Choices
class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED = "EXPIRED", "Expired"


class Booking(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    service = models.ForeignKey(
        "booking.Service",
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    # provider/staff
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_bookings"
    )

    # customer/client
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_bookings"
    )

    date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]

        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["tenant", "date"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "date", "start_time"],
                condition=~Q(status=BookingStatus.CANCELLED),
                name="unique_active_booking_slot"
            )
        ]

    def __str__(self):
        return f"{self.service.name} - {self.date} {self.start_time}"

    def clean(self):
        super().clean()

        # Start/end validation
        if self.start_time >= self.end_time:
            raise ValidationError({
                "end_time": "End time must be after start time."
            })

        now = timezone.localtime()

        # Prevent past booking
        if self.date < now.date():
            raise ValidationError({
                "date": "Cannot book in the past."
            })

        # Prevent past time booking today
        if (
            self.date == now.date()
            and self.start_time <= now.time()
        ):
            raise ValidationError({
                "start_time": "This slot has already passed."
            })

        # Overlap check
        overlapping = Booking.objects.filter(
            user=self.user,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(
            status=BookingStatus.CANCELLED
        ).exclude(
            id=self.id
        )

        if overlapping.exists():
            raise ValidationError(
                "This provider already has a booking during this time."
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        with transaction.atomic():
            return super().save(*args, **kwargs)




class BookingHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="booking_changes"
    )

    previous_status = models.CharField(max_length=20, choices=BookingStatus.choices)
    new_status = models.CharField(max_length=20, choices=BookingStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="notifications")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)



class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["user", "date", "start_time"],
            name="unique_booking_slot"
        )
    ]
def clean(self):
    if self.start_time >= self.end_time:
        raise ValidationError("End time must be after start time")    
            