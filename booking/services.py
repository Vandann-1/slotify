from django.shortcuts import get_object_or_404
from django.db import transaction
from tenants.models import Tenant
from booking.models import BookingStatus
from booking.serializers import BookingSerializer


def create_booking_service(request, slug, data):
    tenant = get_object_or_404( Tenant, slug=slug)
    serializer = BookingSerializer(data=data,
        context={
            "request": request,
            "tenant": tenant  } )
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        booking = serializer.save(status=BookingStatus.CONFIRMED)
    return booking