from datetime import datetime, timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from tenants.models import Tenant

from booking.models import (
    Availability,
    BookingStatus,
)
from booking.serializers import BookingSerializer
from booking.choices import (
    CancelledBy,
    BookingStatus,
)

from booking.models import (
    Booking,
    Availability,
    ACTIVE_BOOKING_STATUSES,

)
from booking.choices import *


def create_booking_service(request, slug, data):
    tenant = get_object_or_404(Tenant,slug=slug)
    service = data.get("service")
    date_str = data.get("date")

    date_obj = datetime.strptime(
        date_str,
        "%Y-%m-%d"
    ).date()
    
    start_time_str = data.get("start_time")

    start_time = datetime.strptime(
    start_time_str,
    "%H:%M:%S"
    ).time()

    weekday = date_obj.weekday()
    availability = (

        Availability.objects.filter(
            tenant=tenant,
            service=service,
            is_active=True,
            date_specific=date_obj
        ).first()

        or

        Availability.objects.filter(
            tenant=tenant,
            service=service,
            is_active=True,
            day_of_week=weekday,
            date_specific__isnull=True
        ).first()

    )

    if not availability:
        raise serializers.ValidationError({
            "error":
            "Service is not available on this day."
        })

    duration = availability.slot_duration

    end_time = (
        datetime.combine(date_obj, start_time)
        + timedelta(minutes=duration)
    ).time()

    if (
        start_time < availability.start_time
        or
        end_time > availability.end_time
    ):

        raise serializers.ValidationError({
            "error":
            "Selected slot is outside business hours."
        })

    serializer = BookingSerializer(
        data=data,
        context={
            "request": request,
            "tenant": tenant,
        }
    )

    serializer.is_valid(
        raise_exception=True
    )

    with transaction.atomic():
        
        overlapping_bookings = Booking.objects.select_for_update().filter(
                provider=availability.user,
                date=date_obj,
                start_time__lt=end_time,
                end_time__gt=start_time,
                status__in=ACTIVE_BOOKING_STATUSES,
                is_deleted=False
            )

        if overlapping_bookings.exists():

            raise serializers.ValidationError({
                "error": "This slot is already booked."
            })





        booking = serializer.save(

            tenant=tenant,
            provider=availability.user,
            customer=request.user,
            end_time=end_time,
            duration_minutes=duration,
            status=BookingStatus.PENDING_PAYMENT
        )

    return booking







def cancel_booking_service(user,booking,reason=None):

    is_customer = booking.customer == user
    is_provider = booking.provider == user
    is_admin = user.is_staff

    if not any([is_customer,is_provider,is_admin]):

        raise serializers.ValidationError({
            "error": "Permission denied"
        })

    if booking.status == BookingStatus.CANCELLED:

        raise serializers.ValidationError({
            "error": "Booking already cancelled"
        })

    if is_customer:
        cancelled_by = CancelledBy.CUSTOMER

    elif is_provider:
        cancelled_by = CancelledBy.PROVIDER

    else:
        cancelled_by = CancelledBy.ADMIN

    booking.cancel(
        cancelled_by=cancelled_by,
        reason=reason
    )

    return booking
