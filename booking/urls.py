from django.urls import path
from .views import *

urlpatterns = [

    # =========================
    # GLOBAL SERVICES
    # =========================

    path("services/",GlobalServiceListView.as_view()),

    # =========================
    # SERVICES
    # =========================

    path( "tenant/<slug:slug>/services/", ServiceListView.as_view()),

    path("tenant/<slug:slug>/services/create/", ServiceCreateView.as_view()),

    # =========================
    # AVAILABILITY
    # =========================

    path("tenant/<slug:slug>/availability/create/",AvailabilityCreateView.as_view()),

    # =========================
    # BOOKINGS
    # =========================

    path(
        "tenant/<slug:slug>/booking/list/",
        BookingListView.as_view()
    ),

    path(
        "tenant/<slug:slug>/booking/slots/",
        AvailableSlotsView.as_view()
    ),

    path(
        "tenant/<slug:slug>/booking/create/",
        BookingCreateView.as_view()
    ),

    path(
        "tenant/<slug:slug>/booking/<uuid:booking_id>/cancel/",
        CancelBookingView.as_view()
    ),

    path(
        "tenant/<slug:slug>/booking/<uuid:booking_id>/update/",
        UpdateBookingView.as_view()
    ),

    path(
        "my-bookings/",
        MyBookingsView.as_view(),
    ),
]