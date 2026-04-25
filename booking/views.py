from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from booking.models import *
from booking.serializers import *
from booking.utils import generate_slots, filter_booked_slots
from rest_framework.permissions import IsAuthenticated


from rest_framework.views import APIView
from .serializers import *


class ServiceCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = Service.objects.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ServiceSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class ServiceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = Service.objects.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


class AvailabilityCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AvailabilitySerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            availability = serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)



class AvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service_id = request.GET.get("service_id")
        date_str = request.GET.get("date")

        if not service_id or not date_str:
            return Response({"error": "service_id and date required"}, status=400)

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format"}, status=400)

        weekday = date_obj.weekday()

        # Check date-specific override
        availability = Availability.objects.filter(
            service_id=service_id,
            date_specific=date_obj,
            is_active=True
        )

        # Fallback to weekly
        if not availability.exists():
            availability = Availability.objects.filter(
                service_id=service_id,
                day_of_week=weekday,
                date_specific__isnull=True,
                is_active=True
            )

        if not availability.exists():
            return Response({"date": str(date_obj), "slots": []})

        # Generate slots
        slots = []
        for avail in availability:
            slots.extend(generate_slots(avail, date_obj))

        # Remove booked slots
        bookings = Booking.objects.filter(
            service_id=service_id,
            date=date_obj,
            status="confirmed"  # adjust based on your model
        )

        available_slots = filter_booked_slots(slots, bookings)

        return Response({
            "date": str(date_obj),
            "slots": available_slots
        })

class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, booked_by=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        booking.status = "CANCELLED"
        booking.save()

        return Response({
            "message": "Booking cancelled successfully"
        })


class UpdateBookingView(APIView):
    permission_classes = [IsAuthenticated]
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

class BookingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.all().order_by("-date")
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)        