from datetime import datetime, timedelta
from rest_framework import serializers
from booking.models import *
from booking.utils import *


# =========================
# BOOKING SERIALIZER
# =========================

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError

from rest_framework import serializers

from .models import Booking, Availability
from .utils import generate_slots


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "service",
            "date",
            "start_time",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "status",
            "end_time",
            "booked_by",
        ]
    def validate(self, data):
        date_obj = data["date"]
        # Monday = 0
        weekday = date_obj.weekday()

        # =========================
        # DATE SPECIFIC AVAILABILITY
        # =========================
        availability_qs = Availability.objects.filter(
            service=data["service"],
            date_specific=date_obj,
            is_active=True,
        )
        # =========================
        # WEEKLY AVAILABILITY
        # =========================
        if not availability_qs.exists():

            availability_qs = Availability.objects.filter(
                service=data["service"],
                day_of_week=weekday,
                date_specific__isnull=True,
                is_active=True,
            )

        availability = availability_qs.first()
        # =========================
        # NOT AVAILABLE
        # =========================

        if not availability:
            raise serializers.ValidationError(
                "Service not available on this day"
            )
        # =========================
        # STORE AVAILABILITY
        # =========================
        data["availability_obj"] = availability
        # PROVIDER INFO
        data["user"] = availability.user
    
        # GENERATE SLOT

        slots = generate_slots(availability, date_obj)
        # =========================
        # END TIME
        # =========================
        duration = availability.slot_duration

        end_time = (datetime.combine( date_obj, data["start_time"])
            +
            timedelta(minutes=duration )).time()
        data["end_time"] = end_time

        # =========================
        # VALID SLOT CHECK
        # =========================

        is_valid = any(s["start_time"] == data["start_time"]

            and

            s["end_time"] == end_time

            for s in slots

        )

        if not is_valid:

            raise serializers.ValidationError(
                "Invalid slot selected"
            )

        return data

    def create(self, validated_data):
        request = self.context["request"]
        # =========================
        # GET AVAILABILITY
        # =========================
        availability = validated_data.pop("availability_obj" )
        print("DEBUG → AVAILABILITY:", availability)
        print("DEBUG → TENANT:",availability.tenant)

        # =========================
        # ASSIGN VALUES
        # =========================

        validated_data["booked_by"] = request.user

        validated_data["tenant"] = (
            availability.tenant
        )

        validated_data["user"] = (
            availability.user
        )

        # =========================
        # CREATE BOOKING
        # =========================

        try:

            booking = Booking(
                **validated_data
            )

            booking.clean()

            booking.save()

            return booking

        except ValidationError as e:

            raise serializers.ValidationError({
                "error": e.messages
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