from datetime import datetime, timedelta


def generate_slots(availability, date):
    """
    this utility function generates time slots based on the availability 
    and date provided. It calculates the start and end datetime objects 
    for the given date and availability, then iteratively creates slots 
    of the specified duration until it reaches the end time. 
    Each slot is represented as a dictionary containing the start and end times.
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
    in this function, we first create a set of booked time ranges from the provided bookings. 
    Then, we filter the generated slots by checking if their start and end times are not in the booked set. 
    This ensures that only available slots are returned, effectively removing any slots that have already been booked
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