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




def get_available_slots( slug,  service_id,  date_str):

    # =====================================
    # VALIDATION
    # =====================================

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

    # =====================================
    # TENANT
    # =====================================

    tenant = get_object_or_404(
        Tenant,
        slug=slug
    )

    weekday = date_obj.weekday() + 1

    # =====================================
    # AVAILABILITY
    # Priority:
    # 1. date_specific
    # 2. recurring weekday
    # =====================================

    availability_qs = Availability.objects.filter(
        tenant=tenant,
        service_id=service_id,
        is_active=True
    )

    availability = (

        availability_qs.filter(
            date_specific=date_obj
        )

        or

        availability_qs.filter(
            day_of_week=weekday,
            date_specific__isnull=True
        )

    )

    # =====================================
    # NO AVAILABILITY
    # =====================================

    if not availability.exists():

        return {
            "date": str(date_obj),
            "slots": [],
            "status": 200
        }

    # =====================================
    # GENERATE SLOTS
    # =====================================

    slots = []

    for avail in availability:

        generated_slots = generate_slots(
            avail,
            date_obj
        )

        slots.extend(generated_slots)

    # =====================================
    # REMOVE BOOKED SLOTS
    # =====================================

    bookings = Booking.objects.filter(
        tenant=tenant,
        service_id=service_id,
        date=date_obj,
        status=BookingStatus.CONFIRMED,
        is_deleted=False
    )

    available_slots = filter_booked_slots(
        slots,
        bookings
    )

    # =====================================
    # REMOVE EXPIRED SLOTS
    # ONLY FOR TODAY
    # =====================================

    now = timezone.localtime()

    buffer_minutes = 5

    current_with_buffer = (
        now + timedelta(minutes=buffer_minutes)
    ).time()

    if date_obj == now.date():

        available_slots = [

            slot for slot in available_slots

            if slot["start_time"] > current_with_buffer
        ]

    # =====================================
    # REMOVE DUPLICATE SLOTS
    # =====================================

    unique_slots = {}

    for slot in available_slots:

        unique_slots[
            slot["start_time"]
        ] = slot

    available_slots = list(
        unique_slots.values()
    )

    # =====================================
    # SORT SLOTS
    # =====================================

    available_slots.sort(
        key=lambda x: x["start_time"]
    )

    # =====================================
    # FORMAT RESPONSE
    # =====================================

    formatted_slots = [

        slot["start_time"].strftime(
            "%H:%M:%S"
        )

        for slot in available_slots
    ]

    # =====================================
    # DEBUG
    # REMOVE LATER
    # =====================================

    print("\n======================")
    print("DATE:", date_obj)
    print("TENANT:", tenant.slug)
    print("TOTAL SLOTS:", len(formatted_slots))
    print("SLOTS:", formatted_slots)
    print("======================\n")

    # =====================================
    # RESPONSE
    # =====================================

    return {
        "date": str(date_obj),
        "slots": formatted_slots,
        "status": 200
    }