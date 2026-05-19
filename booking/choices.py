from django.db import models


# booking/choices.py


class BookingStatus(models.TextChoices):

    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    NO_SHOW = "NO_SHOW", "No Show"
    EXPIRED = "EXPIRED", "Expired"

    RESCHEDULED = "RESCHEDULED", "Rescheduled"


class CancelledBy(models.TextChoices):

    CUSTOMER = "CUSTOMER", "Customer"
    PROVIDER = "PROVIDER", "Provider"
    ADMIN = "ADMIN", "Admin"


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    SYSTEM = "SYSTEM", "System"


class PaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", "Unpaid"
    PAID = "PAID", "Paid"
    PARTIAL_REFUND = "PARTIAL_REFUND", "Partial Refund"
    REFUNDED = "REFUNDED", "Refunded"
    FAILED = "FAILED", "Failed"


class BookingSource(models.TextChoices):
    WEB = "WEB", "Web"
    MOBILE = "MOBILE", "Mobile"
    ADMIN_PANEL = "ADMIN_PANEL", "Admin Panel"
    API = "API", "API"


class RefundStatus(models.TextChoices):
    NOT_REQUIRED = "NOT_REQUIRED", "Not Required"
    PENDING = "PENDING", "Pending"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"

class weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"



from django.db import models


class BookingStatus(models.TextChoices):
    PENDING_PAYMENT = "PENDING_PAYMENT", "Pending Payment"
    CONFIRMED = "CONFIRMED", "Confirmed"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED = "EXPIRED", "Expired"


class CancelledBy(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    PROVIDER = "PROVIDER", "Provider"
    ADMIN = "ADMIN", "Admin"


class PaymentMethod(models.TextChoices):
    CARD = "CARD", "Card"
    UPI = "UPI", "UPI"
    CASH = "CASH", "Cash"


class PaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", "Unpaid"
    PAID = "PAID", "Paid"
    REFUNDED = "REFUNDED", "Refunded"
    PARTIAL_REFUND = "PARTIAL_REFUND", "Partial Refund"


class BookingSource(models.TextChoices):
    WEB = "WEB", "Web"
    MOBILE = "MOBILE", "Mobile"
    ADMIN = "ADMIN", "Admin"


class RefundStatus(models.TextChoices):
    NOT_REQUIRED = "NOT_REQUIRED", "Not Required"
    PENDING = "PENDING", "Pending"
    PROCESSED = "PROCESSED", "Processed"