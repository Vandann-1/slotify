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
    Serializer for managing Booking lifecycle, including automated 
    end-time calculation and availability validation.
    """

    # --- READ-ONLY DISPLAY FIELDS ---
    service_name = serializers.CharField(
        source="service.name", 
        read_only=True
    )
    booked_by = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id", "date", "start_time", "end_time", "status", 
            "created_at", "service", "service_name", "booked_by", "provider"
        ]
        read_only_fields = [
            "id", "end_time", "status", "created_at", 
            "service_name", "booked_by", "provider"
        ]

    # --- USER DATA REPRESENTATION ---
    def get_booked_by(self, obj):
        user = obj.booked_by
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": getattr(user, 'full_name', f"{user.first_name} {user.last_name}"),
        }

    def get_provider(self, obj):
        user = obj.user  # Assuming 'user' field on Booking is the provider
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": getattr(user, 'full_name', f"{user.first_name} {user.last_name}"),
        }

    # --- MAIN VALIDATION LOGIC ---
    def validate(self, data):
        request = self.context.get("request")
        tenant = self.context.get("tenant")
        
        service = data.get("service")
        date_obj = data.get("date")
        start_time = data.get("start_time")

        # 1. Tenant Integrity
        if service.tenant != tenant:
            raise serializers.ValidationError("Service does not belong to this tenant.")

        # 2. Chronological Check
        now = timezone.now()
        if date_obj < now.date():
            raise serializers.ValidationError("Cannot book in the past.")
        
        if date_obj == now.date() and start_time < now.time():
            raise serializers.ValidationError("This time slot has already passed.")

        # 3. Fetch Availability (Priority: Date-specific > Recurring)
        weekday = date_obj.weekday() + 1
        availability_qs = Availability.objects.filter(
            service=service,
            tenant=tenant,
            is_active=True,
        )

        availability = (
            availability_qs.filter(date_specific=date_obj).first() or
            availability_qs.filter(day_of_week=weekday, date_specific__isnull=True).first()
        )

        if not availability:
            raise serializers.ValidationError("Service not available on this day.")

        # 4. Calculation of End Time
        duration = availability.slot_duration
        end_time = (
            datetime.combine(date_obj, start_time) + timedelta(minutes=duration)
        ).time()

        # 5. Business Hours Check
        if start_time < availability.start_time or end_time > availability.end_time:
            raise serializers.ValidationError("Selected time is outside business hours.")

        # 6. Data Preparation for Creation
        data.update({
            "end_time": end_time,
            "user": availability.user,      # Assigning the provider from availability
            "booked_by": request.user,      # Assigning current logged-in user
            "tenant": tenant,
            "availability_obj": availability # Temp helper for create()
        })

        return data

    # --- OBJECT CREATION ---
    def create(self, validated_data):
        # Remove helper from data before model instantiation
        validated_data.pop("availability_obj", None)

        try:
            booking = Booking(**validated_data)
            # Full clean runs model-level validation (like UniqueTogether or overlap checks)
            booking.full_clean()
            booking.save()
            return booking
            
        except DjangoValidationError as e:
            print("FULL CLEAN ERROR:", e)

            if hasattr(e, "message_dict"):
                print("MESSAGE DICT:", e.message_dict)
                raise serializers.ValidationError(e.message_dict)

            print("MESSAGES:", e.messages)
            raise serializers.ValidationError({
                "non_field_errors": e.messages
            })




class ServiceSerializer(
    serializers.ModelSerializer
):

    tenant_name = serializers.CharField(
        source="tenant.name",
        read_only=True
    )

    tenant_slug = serializers.CharField(
        source="tenant.slug",
        read_only=True
    )

    class Meta:

        model = Service

        fields = [
            "id",
            "name",
            "duration",
            "price",
            "tenant_name",
            "tenant_slug",
        ]

# =========================
# AVAILABILITY SERIALIZER (SAFE)
# =========================
class AvailabilitySerializer(serializers.ModelSerializer):

    day_of_week = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    date_specific = serializers.DateField(
        required=False,
        allow_null=True
    )

    class Meta:

        model = Availability

        fields = [
            "service",
            "day_of_week",
            "start_time",
            "end_time",
            "slot_duration",
            "date_specific",
        ]

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

            raise serializers.ValidationError(
                "Missing required fields"
            )

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

    # =========================
    # CREATE
    # =========================

    def create(self, validated_data):

        request = self.context["request"]

        tenant = self.context["tenant"]

        validated_data["user"] = request.user

        validated_data["tenant"] = tenant

        return super().create(validated_data)