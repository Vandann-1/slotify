from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from booking.models import *
from booking.serializers import BookingSerializer
from booking.utils import generate_slots, filter_booked_slots


class AvailableSlotsView(APIView):
    def get(self, request):
        service_id = request.GET.get("service_id")
        date_str = request.GET.get("date")

        # Validate inputs
        if not service_id or not date_str:
            return Response({"error": "service_id and date required"}, status=400)

        # Convert date
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format (YYYY-MM-DD)"}, status=400)

        # Get availability (provider side)
        availability = Availability.objects.filter(
            service_id=service_id,
            is_active=True
        ).first()

        if not availability:
            return Response({"error": "No availability found"}, status=404)

        # Generate slots
        slots = generate_slots(availability, date)

        # Get existing bookings
        bookings = Booking.objects.filter(
            service_id=service_id,
            date=date
        )

        # Filter booked slots
        available_slots = filter_booked_slots(slots, bookings)

        return Response({
            "date": str(date),
            "slots": available_slots
        })


class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            booking = serializer.save()
            return Response({
                "message": "Booking created successfully",
                "data": BookingSerializer(booking).data
            }, status=201)

        return Response(serializer.errors, status=400)


class CancelBookingView(APIView):
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        booking.status = "CANCELLED"
        booking.save()

        return Response({
            "message": "Booking cancelled successfully"
        })


class UpdateBookingView(APIView):
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        serializer = BookingSerializer(
            booking,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            updated_booking = serializer.save()
            return Response({
                "message": "Booking updated successfully",
                "data": BookingSerializer(updated_booking).data
            })

        return Response(serializer.errors, status=400)