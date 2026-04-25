import uuid
from django.db import models
from django.conf import settings
from tenants.models import Tenant
from booking.choices import BookingStatus
from django.core.exceptions import ValidationError
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


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
    Tenant,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration = models.IntegerField(help_text="In minutes (e.g., 30)")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class Availability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
    Tenant,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)   
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availabilities")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="availabilities")
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        null=True,
        blank=True
)
    date_specific = models.DateField(null=True, blank=True, help_text="Overrides day_of_week if set")
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    slot_duration = models.IntegerField(help_text="In minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=False, blank=False, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")  # provider
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booked_appointments")  # client
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
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date", "start_time"],
                name="unique_booking_slot"
            )
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

        overlapping = Booking.objects.filter(
        user=self.user,
        date=self.date,
        start_time__lt=self.end_time,
        end_time__gt=self.start_time,
    ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("This slot is already booked")
        overlapping = Booking.objects.filter(
        user=self.user,
        date=self.date,
        start_time__lt=self.end_time,
        end_time__gt=self.start_time,
    ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("This slot is already booked")
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

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
            