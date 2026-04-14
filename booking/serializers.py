from datetime import datetime, timedelta
from rest_framework import serializers
from booking.models import *
from booking.utils import *


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["service", "date", "start_time"]
        read_only_fields = ["id", "tenant", "created_at", "status", "end_time", "booked_by"]

    def validate(self, data):
        request = self.context["request"]

        # Get availability
        availability = Availability.objects.filter(
            service=data["service"],
            is_active=True
        ).first()

        if not availability:
            raise serializers.ValidationError("No availability found")

        # Assign provider automatically
        data["user"] = availability.user

        # Check day
        if data["date"].weekday() != availability.day_of_week:
            raise serializers.ValidationError("Service not available on this day")

        # Generate slots
        slots = generate_slots(availability, data["date"])

        # Calculate end_time
        duration = availability.slot_duration
        calculated_end = (
            datetime.combine(data["date"], data["start_time"]) +
            timedelta(minutes=duration)
        ).time()

        data["end_time"] = calculated_end

        # Validate slot
        valid_slot = any(
            s["start_time"] == data["start_time"] and
            s["end_time"] == data["end_time"]
            for s in slots
        )

        if not valid_slot:
            raise serializers.ValidationError("Invalid slot selected")

        return data

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["tenant"] = validated_data["service"].tenant
        validated_data["booked_by"] = request.user
        return super().create(validated_data)

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields =["id", "tenant", "created_at"]
    ''' this def is help to create service with tenant and created_by field automatically from request user '''
    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["tenant"] = None
        validated_data["created_by"] = request.user
        return super().create(validated_data)

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = "__all__"
        read_only_fields = ["id", "tenant", "created_at"]
    ''' this def is help to create availability with tenant and user field automatically from request user '''
    def create(self, validated_data):
        request = self.context["request"]
        validated_data["tenant"] = validated_data["service"].tenant
        validated_data["user"] = request.user
        return super().create(validated_data)        
    

