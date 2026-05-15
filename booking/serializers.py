from datetime import datetime, timedelta
from rest_framework import serializers
from booking.models import *
from booking.utils import *
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidation
from rest_framework import serializers

from .models import Booking, Availability
from .utils import generate_slots

from rest_framework import serializers
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Booking, Availability, BookingStatus


# =========================
# BOOKING SERIALIZER
# =========================



class BookingSerializer(serializers.ModelSerializer):
    """
    Booking Serializer

    Responsibilities:
    • Validate booking request
    • Validate availability
    • Auto-calculate end time
    • Assign provider/customer automatically
    • Prevent invalid booking creation
    """

    # =====================================================
    # READ-ONLY DISPLAY FIELDS
    # =====================================================

    service_name = serializers.CharField(
        source="service.name",
        read_only=True
    )

    customer = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()

    # =====================================================
    # META
    # =====================================================

    class Meta:
        model = Booking

        fields = [  "id",   "date",   "start_time",  "end_time", "status",
             "created_at", "service","service_name",  "customer", "provider",]

        read_only_fields = [
            "id",
            "end_time",
            "status",
            "created_at",
            "service_name",
            "customer",
            "provider",
        ]

    # =====================================================
    # CUSTOMER REPRESENTATION
    # =====================================================

    def get_customer(self, obj):

        customer = obj.customer

        if not customer:
            return None

        return {
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "full_name": getattr(
                customer,
                "full_name",
                f"{customer.first_name} {customer.last_name}"
            ),
        }

    # =====================================================
    # PROVIDER REPRESENTATION
    # =====================================================

    def get_provider(self, obj):

        provider = obj.provider

        if not provider:
            return None

        return {
            "id": provider.id,
            "username": provider.username,
            "email": provider.email,
            "full_name": getattr(
                provider,
                "full_name",
                f"{provider.first_name} {provider.last_name}"
            ),
        }

    # =====================================================
    # MAIN VALIDATION LOGIC
    # =====================================================

    def validate(self, data):

        request = self.context.get("request")
        tenant = self.context.get("tenant")

        service = data.get("service")
        date_obj = data.get("date")
        start_time = data.get("start_time")

        # -------------------------------------------------
        # 1. TENANT VALIDATION
        # -------------------------------------------------

        if service.tenant != tenant:

            raise serializers.ValidationError(
                "Service does not belong to this workspace."
            )

        # -------------------------------------------------
        # 2. PAST DATE/TIME VALIDATION
        # -------------------------------------------------

        now = timezone.localtime()

        if date_obj < now.date():

            raise serializers.ValidationError(
                "Cannot create booking in the past."
            )

        appointment_datetime = datetime.combine(
            date_obj,
            start_time
        )

        appointment_datetime = timezone.make_aware(
            appointment_datetime
        )

        buffer_minutes = 2

        minimum_booking_time = (
            now + timedelta(
                minutes=buffer_minutes
            )
        )

        if appointment_datetime <= minimum_booking_time:

            raise serializers.ValidationError(
                {
                    "start_time":
                    (
                        f"Bookings must be made at least "
                        f"{buffer_minutes} minutes in advance."
                    )
                }
            )

        # -------------------------------------------------
        # 3. FIND AVAILABILITY
        # Priority:
        # Date-specific > recurring weekday
        # -------------------------------------------------

        weekday = date_obj.weekday() + 1

        availability_qs = Availability.objects.filter(
            service=service,
            tenant=tenant,
            is_active=True,
        )

        availability = (

            availability_qs.filter(
                date_specific=date_obj
            ).first()

            or

            availability_qs.filter(
                day_of_week=weekday,
                date_specific__isnull=True
            ).first()

        )

        # -------------------------------------------------
        # 4. AVAILABILITY CHECK
        # -------------------------------------------------

        if not availability:

            raise serializers.ValidationError(
                "Service is not available on this day."
            )

        # -------------------------------------------------
        # 5. CALCULATE END TIME
        # -------------------------------------------------

        duration = availability.slot_duration

        end_time = (

            datetime.combine(
                date_obj,
                start_time
            )

            +

            timedelta(minutes=duration)

        ).time()

        # -------------------------------------------------
        # 6. BUSINESS HOURS VALIDATION
        # -------------------------------------------------

        if (
            start_time < availability.start_time
            or
            end_time > availability.end_time
        ):

            raise serializers.ValidationError(
                "Selected slot is outside business hours."
            )

        # -------------------------------------------------
        # 7. PREPARE BOOKING DATA
        # -------------------------------------------------

        data.update({

            # Auto-generated end time
            "end_time": end_time,

            # Workspace / tenant
            "tenant": tenant,

            # Provider / professional
            "provider": availability.user,

            # Logged-in customer/client
            "customer": request.user,

            # Auto-confirm booking
            "status": BookingStatus.CONFIRMED,

            # Helper object (removed later)
            "availability_obj": availability,
        })

        return data

    # =====================================================
    # CREATE BOOKING
    # =====================================================

    def create(self, validated_data):

        # Remove temporary helper
        validated_data.pop(
            "availability_obj",
            None
        )

        try:

            booking = Booking(
                **validated_data
            )

            # Run model-level validation
            booking.full_clean()

            # Save booking
            booking.save()

            return booking

        except DjangoValidationError as e:
            print("\n==============================")
            print("BOOKING VALIDATION ERROR")
            print("==============================")

            if hasattr(e, "message_dict"):

                print("MESSAGE DICT:")
                print(e.message_dict)

                raise serializers.ValidationError(
                    e.message_dict
                )

            print("MESSAGES:")
            print(e.messages)

            raise serializers.ValidationError({
                "non_field_errors": e.messages
            })
        


class CancelBookingSerializer(serializers.Serializer):

    # Optional cancellation reason
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


class ServiceSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name",read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug",read_only=True)

    class Meta:
        model = Service
        fields = [ "id", "name", "duration","price","tenant_name","tenant_slug",]

# =========================
# AVAILABILITY SERIALIZER (SAFE)
# =========================

class AvailabilitySerializer(serializers.ModelSerializer):
    day_of_week = serializers.IntegerField(required=False,allow_null=True)
    date_specific = serializers.DateField(required=False,allow_null=True)

    class Meta:
        model = Availability
        fields = ["service", "day_of_week", "start_time","end_time","slot_duration", "date_specific",]

    # =========================
    # VALIDATE
    # =========================

    def validate(self, data):
        request = self.context["request"]
        user = request.user
        service = data.get("service")
        day = data.get("day_of_week")
        date = data.get("date_specific")
        start = data.get("start_time")
        end = data.get("end_time")

        # REQUIRED
        if not service or not start or not end:
            raise serializers.ValidationError("Missing required fields")

        # ONLY ONE
        if (
            (day is None and date is None)
            or
            (day is not None and date is not None)
        ):

            raise serializers.ValidationError(
                "Provide either day_of_week OR date_specific"
            )

        # TIME CHECK
        if start >= end:
            raise serializers.ValidationError(
                "End time must be after start time"
            )

        # OVERLAP CHECK
        qs = Availability.objects.filter(
            user=user,
            service=service,
            is_active=True
        )

        if date:
            qs = qs.filter(
                date_specific=date
            )

        else:
            qs = qs.filter(
                day_of_week=day,
                date_specific__isnull=True
            )

        for avail in qs:
            if not (
                end <= avail.start_time
                or
                start >= avail.end_time
            ):

                raise serializers.ValidationError(
                    "Availability overlap exists"
                )
        return data

    #CREATE AVAILABILITY
    def create(self, validated_data):
        request = self.context["request"]
        tenant = self.context["tenant"]
        validated_data["user"] = request.user
        validated_data["tenant"] = tenant
        return super().create(validated_data)