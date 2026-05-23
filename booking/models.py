import uuid
from decimal import Decimal
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from django.utils import timezone

from tenants.models import Tenant

from .choices import (
    BookingStatus,
    CancelledBy,
    PaymentMethod,
    PaymentStatus,
    BookingSource,
    RefundStatus,
)


User = settings.AUTH_USER_MODEL


ACTIVE_BOOKING_STATUSES = [
    BookingStatus.PENDING_PAYMENT,
    BookingStatus.CONFIRMED,
]


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
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="services"
    )

    name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    duration = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Availability(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        null=True,
        blank=True
    )

    date_specific = models.DateField(
        null=True,
        blank=True,
        help_text="Overrides recurring availability"
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    slot_duration = models.PositiveIntegerField(
        help_text="Slot duration in minutes"
    )

    buffer_before = models.PositiveIntegerField(
        default=0,
        help_text="Buffer before booking in minutes"
    )

    buffer_after = models.PositiveIntegerField(
        default=0,
        help_text="Buffer after booking in minutes"
    )

    max_bookings_per_slot = models.PositiveIntegerField(
        default=1
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["start_time"]

        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["service"]),
            models.Index(fields=["user"]),
            models.Index(fields=["day_of_week"]),
            models.Index(fields=["date_specific"]),
            models.Index(fields=["is_active"]),
        ]

    def clean(self):
        super().clean()

        if self.start_time >= self.end_time:
            raise ValidationError({
                "end_time": "End time must be after start time."
            })

        if self.day_of_week is None and self.date_specific is None:
            raise ValidationError(
                "Provide either day_of_week or date_specific."
            )

        if self.day_of_week is not None and self.date_specific is not None:
            raise ValidationError(
                "Cannot use both day_of_week and date_specific."
            )

    def __str__(self):
        return f"{self.service.name} Availability"


class Booking(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_bookings"
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_bookings"
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    duration_minutes = models.PositiveIntegerField(
        default=30
    )

    status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING_PAYMENT
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )

    refund_status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.NOT_REQUIRED
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    booking_source = models.CharField(
        max_length=20,
        choices=BookingSource.choices,
        default=BookingSource.WEB
    )

    locked_until = models.DateTimeField(null=True,blank=True)
    expires_at = models.DateTimeField(null=True,blank=True)
    confirmed_at = models.DateTimeField(null=True,blank=True)


    completed_at = models.DateTimeField(null=True,blank=True)
    checked_in_at = models.DateTimeField(null=True,blank=True)
    cancelled_at = models.DateTimeField( null=True,blank=True)
    cancelled_by = models.CharField(max_length=20,choices=CancelledBy.choices,null=True,blank=True)
    cancellation_reason = models.TextField(null=True,blank=True)
    notes = models.TextField(blank=True,null=True)
    internal_notes = models.TextField(blank=True,null=True)

    rescheduled_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_bookings"
    )

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "-date",
            "-start_time"
        ]

        indexes = [
            models.Index(fields=["tenant", "date"]),
            models.Index(fields=["provider", "date"]),
            models.Index(fields=["customer", "date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_deleted"]),
        ]

        constraints = [
            models.CheckConstraint(
                check=Q(end_time__gt=F("start_time")),
                name="booking_end_after_start"
            ),

            models.UniqueConstraint(
                fields=[
                    "provider",
                    "date",
                    "start_time"
                ],
                condition=Q(
                    status__in=ACTIVE_BOOKING_STATUSES,
                    is_deleted=False
                ),
                name="unique_active_provider_booking_slot"
            )
        ]

    def __str__(self):
        return (
            f"{self.service.name} | "
            f"{self.customer} | "
            f"{self.date} {self.start_time}"
        )

    @property
    def is_active(self):
        return self.status in ACTIVE_BOOKING_STATUSES

    @property
    def is_cancelled(self):
        return self.status == BookingStatus.CANCELLED

    @property
    def is_completed(self):
        return self.status == BookingStatus.COMPLETED

    @property
    def can_be_cancelled(self):
        return self.status in [
            BookingStatus.PENDING_PAYMENT,
            BookingStatus.CONFIRMED,
        ]

    def clean(self):
        super().clean()

        now = timezone.localtime()

        if self.start_time >= self.end_time:
            raise ValidationError({
                "end_time": "End time must be after start time."
            })

        if self._state.adding:

            if self.date < now.date():
                raise ValidationError({
                    "date": "Cannot create booking in the past."
                })

            appointment_datetime = datetime.combine(
                self.date,
                self.start_time
            )

            appointment_datetime = timezone.make_aware(
                appointment_datetime
            )

            minimum_booking_time = (
                now + timedelta(minutes=2)
            )

            if appointment_datetime <= minimum_booking_time:
                raise ValidationError({
                    "start_time":
                    "This slot is no longer available."
                })

        overlapping_bookings = Booking.objects.filter(
            provider=self.provider,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=ACTIVE_BOOKING_STATUSES,
            is_deleted=False
        ).exclude(
            id=self.id
        )

        if overlapping_bookings.exists():
            raise ValidationError({
                "non_field_errors":
                "Provider already has another booking during this time."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def mark_confirmed(self):
        old_status = self.status
        self.status = BookingStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()
        self.history.create(
        previous_status=old_status,
        new_status=self.status
    )

    def mark_completed(self):
        self.status = BookingStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def mark_expired(self):
        self.status = BookingStatus.EXPIRED
        self.save()

    def cancel(self, cancelled_by, reason=None):

        if not self.can_be_cancelled:
            raise ValidationError("This booking cannot be cancelled.")

        appointment_datetime = datetime.combine(self.date,self.start_time)
        appointment_datetime = timezone.make_aware(appointment_datetime)

        current_time = timezone.now()
        if appointment_datetime < current_time:
            raise ValidationError("Past appointments cannot be cancelled.")

        time_difference = (appointment_datetime - current_time)

        if time_difference < timedelta(hours=1):
            raise ValidationError("Cannot cancel within 1 hour of appointment.")

        self.status = BookingStatus.CANCELLED
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.save()


class BookingHistory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="history"
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="booking_changes"
    )

    previous_status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices
    )

    new_status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.booking.id} | "
            f"{self.previous_status} → {self.new_status}"
        )


class Notification(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user}"