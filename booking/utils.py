from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from tenants.models import *
from booking.models import *
# from booking.utils import generate_slots, filter_booked_slots




def filter_booked_slots(slots, bookings):

    """
    Remove slots that overlap with any existing booking
    """

    filtered = []

    for slot in slots:
        slot_start = slot["start_time"]
        slot_end = slot["end_time"]

        overlap_found = False

        for booking in bookings:
            if has_overlap(
                slot_start,
                slot_end,
                booking.start_time,
                booking.end_time
            ):
                overlap_found = True
                break

        if not overlap_found:
            filtered.append(slot)

    return filtered

def has_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1

def generate_slots(availability, date):
    slots = []

    start_dt = datetime.combine(date, availability.start_time)
    end_dt = datetime.combine(date, availability.end_time)

    duration = timedelta(minutes=availability.slot_duration)

    current = start_dt

    while current + duration <= end_dt:
        slot_start = current.time()
        slot_end = (current + duration).time()

        slots.append({
            "start_time": slot_start,
            "end_time": slot_end,
        })

        current += duration

    return slots


def get_available_slots(slug, service_id, date_str):

    if not service_id or not date_str:
        return {
            "error": "service_id and date required",
            "status": 400
        }

    try:
        date_obj = datetime.strptime(
            date_str,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return {
            "error": "Invalid date format",
            "status": 400
        }

    weekday = date_obj.weekday() + 1

    tenant = get_object_or_404(
        Tenant,
        slug=slug
    )

    availability = Availability.objects.filter(
        tenant=tenant,
        service_id=service_id,
        date_specific=date_obj,
        is_active=True
    )

    if not availability.exists():

        availability = Availability.objects.filter(
            tenant=tenant,
            service_id=service_id,
            day_of_week=weekday,
            date_specific__isnull=True,
            is_active=True
        )

    if not availability.exists():

        return {
            "date": str(date_obj),
            "slots": [],
            "status": 200
        }

    slots = []

    for avail in availability:

        slots.extend(
            generate_slots(
                avail,
                date_obj
            )
        )

    bookings = Booking.objects.filter(
        tenant=tenant,
        service_id=service_id,
        date=date_obj,
        status="confirmed"
    )

    available_slots = filter_booked_slots(
        slots,
        bookings
    )

    formatted_slots = [

        slot["start_time"].strftime("%H:%M:%S")

        for slot in available_slots
    ]

    return {
        "date": str(date_obj),
        "slots": formatted_slots,
        "status": 200
    }    