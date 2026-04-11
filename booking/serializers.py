from django.conf import settings
from tenants.models import Tenant
from booking.choices import BookingStatus
from rest_framework import serializers
from booking.models import *

User = settings.AUTH_USER_MODEL

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields =["id", "tenant", "created_at"]
    ''' this def is help to create service with tenant and created_by field automatically from request user '''
    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["tenant"] = request.user.current_tenant
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
        validated_data["tenant"] = request.user.current_tenant
        validated_data["user"] = request.user
        return super().create(validated_data)        
    


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["id", "tenant", "created_at", "status"]
    ''' this def is help to validate booking with tenant and booked_by field automatically from request user ''' 
    def validate(self, data):
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("Invalid time range")
        return data
    ''' this def is help to create booking with tenant and booked_by field automatically from request user '''
    def create(self, validated_data):
        request = self.context["request"]
        validated_data["tenant"] = request.user.current_tenant
        validated_data["booked_by"] = request.user
        return super().create(validated_data)    