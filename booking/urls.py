from django.urls import path 
from .views import *






urlpatterns = [
    path("booking/slots/", AvailableSlotsView.as_view()),
    path("booking/create/", BookingCreateView.as_view()),
    path("booking/<uuid:booking_id>/cancel/", CancelBookingView.as_view()),
    path("booking/<uuid:booking_id>/update/", UpdateBookingView.as_view()),

]
