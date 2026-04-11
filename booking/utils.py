from datetime import datetime, timedelta


def generate_slots(availability, date):
    """
    Generate slots for a given availability and date
    """

    slots = []

    start_dt = datetime.combine(date, availability.start_time)
    end_dt = datetime.combine(date, availability.end_time)

    duration = timedelta(minutes=availability.slot_duration)

    current = start_dt

    while current + duration <= end_dt:
        slots.append({
            "start_time": current.time(),
            "end_time": (current + duration).time(),
        })
        current += duration

    return slots


def filter_booked_slots(slots, bookings):
    """
    Remove already booked slots
    """

    booked_set = set(
        (b.start_time, b.end_time)
        for b in bookings
    )

    return [
        slot for slot in slots
        if (slot["start_time"], slot["end_time"]) not in booked_set
    ]


def has_overlap(start1, end1, start2, end2):
    """
    Check if two time ranges overlap
    """
    return start1 < end2 and start2 < end1