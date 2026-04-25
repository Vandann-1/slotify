from datetime import datetime, timedelta
from rest_framework import serializers
from booking.models import *
from booking.utils import *


# =========================
# BOOKING SERIALIZER
# =========================

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["service", "date", "start_time"]
        read_only_fields = ["id", "created_at", "status", "end_time", "booked_by"]

    def validate(self, data):
        date_obj = data["date"]
        weekday = date_obj.weekday()

        # 🔥 1. Get correct availability
        availability_qs = Availability.objects.filter(
            service=data["service"],
            date_specific=date_obj,
            is_active=True
        )

        if not availability_qs.exists():
            availability_qs = Availability.objects.filter(
                service=data["service"],
                day_of_week=weekday,
                date_specific__isnull=True,
                is_active=True
            )

        availability = availability_qs.first()

        if not availability:
            raise serializers.ValidationError("Service not available on this day")

        # 🔥 2. Store availability for create()
        data["availability_obj"] = availability

        # 🔥 3. Assign provider
        data["user"] = availability.user

        # 🔥 4. Generate slots
        slots = generate_slots(availability, date_obj)

        # 🔥 5. Calculate end time
        duration = availability.slot_duration
        end_time = (
            datetime.combine(date_obj, data["start_time"]) +
            timedelta(minutes=duration)
        ).time()

        data["end_time"] = end_time

        # 🔥 6. Validate slot
        is_valid = any(
            s["start_time"] == data["start_time"] and
            s["end_time"] == end_time
            for s in slots
        )

        if not is_valid:
            raise serializers.ValidationError("Invalid slot selected")

        return data

    def create(self, validated_data):

        request = self.context["request"]

        # 🔥 Get stored availability
        availability = validated_data.pop("availability_obj")

        print("DEBUG → AVAILABILITY:", availability)
        print("DEBUG → TENANT:", availability.tenant)

        validated_data["booked_by"] = request.user
        validated_data["tenant"] = availability.tenant   # ✅ FIXED
        validated_data["user"] = availability.user       # provider

        return super().create(validated_data)




# =========================
# SERVICE SERIALIZER (FIXED)
# =========================
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "duration", "price"]

    # ❌ NO custom create (avoids 500 error)


# =========================
# AVAILABILITY SERIALIZER (SAFE)
# =========================
class AvailabilitySerializer(serializers.ModelSerializer):
    day_of_week = serializers.IntegerField(required=False, allow_null=True)
    date_specific = serializers.DateField(required=False, allow_null=True)

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

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        service = data.get("service")
        day = data.get("day_of_week")
        date = data.get("date_specific")
        start = data.get("start_time")
        end = data.get("end_time")

        # 🔴 Basic required checks
        if not service or not start or not end:
            raise serializers.ValidationError("Missing required fields")

        # 🔒 Rule 1: Only one of day OR date
        if (day is None and date is None) or (day is not None and date is not None):
            raise serializers.ValidationError(
                "Provide either day_of_week OR date_specific, not both."
            )

        # 🔒 Rule 2: Time validation
        if start >= end:
            raise serializers.ValidationError("End time must be after start time")

        # 🔒 Rule 3: Prevent overlapping
        qs = Availability.objects.filter(
            user=user,
            service=service,
            is_active=True
        )

        if date:
            qs = qs.filter(date_specific=date)
        else:
            qs = qs.filter(day_of_week=day, date_specific__isnull=True)

        for avail in qs:
            if not (end <= avail.start_time or start >= avail.end_time):
                raise serializers.ValidationError(
                    "This time overlaps with existing availability"
                )

        return data

    def create(self, validated_data):
        request = self.context["request"]

        # 🔴 HARD CHECK (this was missing)
        if not hasattr(request.user, "tenant") or request.user.tenant is None:
            raise serializers.ValidationError("User must belong to a tenant")

        validated_data["user"] = request.user
        validated_data["tenant"] = request.user.tenant  # ✅ guaranteed now

        return super().create(validated_data)