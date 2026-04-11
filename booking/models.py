import uuid
from django.db import models
from django.conf import settings
from tenants.models import Tenant
from booking.choices import BookingStatus


User = settings.AUTH_USER_MODEL


class Availability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="availabilities")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availabilities")
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(help_text="In minutes (e.g., 30)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Booking(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")  # person being booked
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booked_appointments")  # client
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)