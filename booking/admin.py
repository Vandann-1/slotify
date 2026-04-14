from django.contrib import admin

# Register your models here.
from django.contrib import admin
from booking.models import Service, Availability, Booking, BookingHistory, Notification


admin.site.register(Service)
admin.site.register(Availability)
admin.site.register(Booking)
admin.site.register(BookingHistory)
admin.site.register(Notification)