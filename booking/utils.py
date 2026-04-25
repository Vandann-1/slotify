from datetime import datetime, timedelta



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