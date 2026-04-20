from django.urls import path 
from .views import *






urlpatterns = [

    path("services/", ServiceListView.as_view()),        # GET
    path("services/create/", ServiceCreateView.as_view()),  # POST

    # 🔥 AVAILABILITY
    path("availability/", AvailabilityCreateView.as_view()),
    path("booking/list/", BookingListView.as_view()),


    path("booking/slots/", AvailableSlotsView.as_view()),
    path("booking/create/", BookingCreateView.as_view()),
    path("booking/<uuid:booking_id>/cancel/", CancelBookingView.as_view()),
    path("booking/<uuid:booking_id>/update/", UpdateBookingView.as_view()),

]
