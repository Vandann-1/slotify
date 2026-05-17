import uuid
from django.db import models
from django.conf import settings
from tenants.models import Tenant
from booking.choices import BookingStatus
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.conf import settings  # Import settings for the User model
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .choices import (
    BookingStatus,
    CancelledBy,
    PaymentMethod,
    PaymentStatus,
    BookingSource,
    RefundStatus
)





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
# booking/models.py



from .choices import (
    BookingStatus,
    CancelledBy,
    PaymentStatus,
    BookingSource,
    RefundStatus,
)


ACTIVE_BOOKING_STATUSES = [
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
]


class Booking(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # =========================
    # RELATIONS
    # =========================

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

    # admin/professional / Provider
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_bookings"
    )

    # Customer / Client
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_bookings"
    )

    # =========================
    # BOOKING DATETIME
    # =========================

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(
        default=30
    )

    # =========================
    # BOOKING STATUS
    # =========================

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    # =========================
    # PAYMENT
    # =========================

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
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

    # =========================
    # CANCELLATION
    # =========================

    cancelled_by = models.CharField(max_length=20,choices=CancelledBy.choices,null=True,blank=True)

    cancellation_reason = models.TextField(
        null=True,
        blank=True
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # =========================
    # EXTRA METADATA
    # =========================

    booking_source = models.CharField(
        max_length=20,
        choices=BookingSource.choices,
        default=BookingSource.WEB
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    internal_notes = models.TextField(
        blank=True,
        null=True
    )

    rescheduled_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_bookings"
    )

    # =========================
    # TIMESTAMPS
    # =========================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    is_deleted = models.BooleanField(default=False)


# =============================
    checked_in_at = models.DateTimeField(
    null=True,
    blank=True
)



    # =========================
    # META
    # =========================

    class Meta:
        ordering = [
            "-date",
            "-start_time"
        ]

        indexes = [
            models.Index(
                fields=["tenant", "date"]
            ),

            models.Index(
                fields=["provider", "date"]
            ),

            models.Index(
                fields=["customer", "date"]
            ),

            models.Index(
                fields=["status"]
            ),

            models.Index(
                fields=["payment_status"]
            ),
        ]

        constraints = [

            # Prevent active overlapping booking
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

    # =========================
    # STRING REPRESENTATION
    # =========================

    def __str__(self):

        return (
            f"{self.service.name} | "
            f"{self.customer} | "
            f"{self.date} {self.start_time}"
        )

    # =========================
    # MODEL VALIDATION
    # =========================

    def clean(self):
        super().clean()
        now = timezone.localtime()

        # -------------------------
        # Time Validation
        # -------------------------

        if self.start_time >= self.end_time:

            raise ValidationError({
                "end_time":
                "End time must be after start time."
            })

        # -------------------------
        # Past Date Validation
        # -------------------------
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

        # -------------------------
        # Overlap Validation
        # -------------------------

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

    # =========================
    # SAVE
    # =========================

    def save(self, *args, **kwargs):
        with transaction.atomic():
            return super().save(*args, **kwargs)

    # =========================
    # BUSINESS METHODS
    # =========================

    @property
    def is_cancelled(self):
        return self.status == BookingStatus.CANCELLED

    @property
    def is_completed(self):
        return self.status == BookingStatus.COMPLETED

    @property
    def is_active(self):
        return self.status in ACTIVE_BOOKING_STATUSES

    @property
    def can_be_cancelled(self):
        return self.status in [
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED
        ]
    def cancel(
        self,
        cancelled_by,
        reason=None
    ):

        # =====================================
        # STATUS VALIDATION
        # =====================================

        if not self.can_be_cancelled:

            raise ValidationError(
                "This booking cannot be cancelled."
            )

        # =====================================
        # CANCELLATION WINDOW CHECK
        # =====================================

        appointment_datetime = datetime.combine(
            self.date,
            self.start_time
        )

        appointment_datetime = timezone.make_aware(
            appointment_datetime
        )

        current_time = timezone.now()

        # -------------------------------------
        # Past appointment check
        # -------------------------------------

        if appointment_datetime < current_time:

            raise ValidationError(
                "Past appointments cannot be cancelled."
            )

        # -------------------------------------
        # 1-hour cancellation restriction
        # -------------------------------------

        time_difference = (
            appointment_datetime - current_time
        )

        if time_difference < timedelta(hours=1):

            raise ValidationError(
                "Cannot cancel within 1 hour of appointment."
            )
        # =====================================
        # CANCEL BOOKING
        # =====================================

        self.status = BookingStatus.CANCELLED

        self.cancelled_by = cancelled_by

        self.cancellation_reason = reason

        self.cancelled_at = timezone.now()

        self.save()

    def mark_completed(self):
        self.status = BookingStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def mark_confirmed(self):
        self.status = BookingStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()




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
            