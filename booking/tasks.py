from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from booking.models import Booking
from booking.models import BookingStatus


@shared_task
def expire_pending_bookings():

    expired_time = timezone.now() - timedelta(minutes=15)

    bookings = Booking.objects.filter(
        status=BookingStatus.PENDING_PAYMENT,
        created_at__lte=expired_time
    )

    for booking in bookings:

        booking.status = BookingStatus.EXPIRED

        booking.save()