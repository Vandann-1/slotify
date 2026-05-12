from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from tenants.models import *
from booking.models import *
from booking.serializers import *
from booking.utils import generate_slots, filter_booked_slots
from rest_framework.permissions import IsAuthenticated
from django.db import transaction


from rest_framework.views import APIView
from .serializers import *


# =========================
# SERVICE LIST
# =========================

class ServiceListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):

        tenant = get_object_or_404(
            Tenant,
            slug=slug
        )

        services = Service.objects.filter(
            tenant=tenant
        )

        serializer = ServiceSerializer(
            services,
            many=True
        )

        return Response(
            serializer.data
        )


# =========================
# SERVICE CREATE
# =========================

class ServiceCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, slug):

        tenant = get_object_or_404(
            Tenant,
            slug=slug
        )

        serializer = ServiceSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save(
                tenant=tenant
            )

            return Response(
                serializer.data,
                status=201
            )

        return Response(
            serializer.errors,
            status=400
        )

from django.shortcuts import get_object_or_404

class AvailabilityCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug)

        #  Only owner can create
        if tenant.owner != request.user:
            return Response({"error": "Not allowed"}, status=403)

        data = request.data.copy()

        #  Force tenant
        data["tenant"] = tenant.id

        #  Validate service belongs to same tenant
        service = get_object_or_404(Service, id=data.get("service"))

        if service.tenant != tenant:
            return Response(
                {"error": "Service does not belong to this tenant"},
                status=400
            )

        serializer = AvailabilitySerializer(
            data=data,
            context={"request": request, "tenant": tenant}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)  # 🔒 force user
            return Response(serializer.data, status=201)

        print("SERIALIZER ERRORS:", serializer.errors)

        return Response(serializer.errors, status=400)
    








class AvailableSlotsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):

        service_id = request.GET.get("service_id")
        date_str = request.GET.get("date")

        if not service_id or not date_str:
            return Response(
                {"error": "service_id and date required"},
                status=400
            )

        try:
            date_obj = datetime.strptime(
                date_str,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return Response(
                {"error": "Invalid date format"},
                status=400
            )

        # Monday=1 Sunday=7
        weekday = date_obj.weekday() + 1

        tenant = get_object_or_404(
            Tenant,
            slug=slug
        )

        print("SERVICE:", service_id)
        print("DATE:", date_obj)
        print("WEEKDAY:", weekday)

        # Date specific
        availability = Availability.objects.filter(
            tenant=tenant,
            service_id=service_id,
            date_specific=date_obj,
            is_active=True
        )

        # Weekly fallback
        if not availability.exists():

            availability = Availability.objects.filter(
                tenant=tenant,
                service_id=service_id,
                day_of_week=weekday,
                date_specific__isnull=True,
                is_active=True
            )

        print("AVAILABILITY:", availability)

        if not availability.exists():
            return Response({
                "date": str(date_obj),
                "slots": []
            })

        slots = []

        for avail in availability:
            slots.extend(
                generate_slots(
                    avail,
                    date_obj
                )
            )

        bookings = Booking.objects.filter(
            tenant=tenant,
            service_id=service_id,
            date=date_obj,
            status="confirmed"
        )

        available_slots = filter_booked_slots(
            slots,
            bookings
        )

        print("FINAL SLOTS:", available_slots)



        formatted_slots = [

            slot["start_time"].strftime(
                "%H:%M:%S"
            )

            for slot in available_slots

        ]

        return Response({

            "date": str(date_obj),

            "slots": formatted_slots

        })
            


class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        # 1. TENANT VALIDATION (Ensures the URL slug matches a real tenant)
        tenant = get_object_or_404(Tenant, slug=slug)

        # 2. INITIALIZE SERIALIZER 
        # We pass tenant and user in context so the serializer can perform 
        # complex cross-field validations (Overlap, Ownership, etc.)
        serializer = BookingSerializer(
            data=request.data, 
            context={'request': request, 'tenant': tenant}
        )

        if serializer.is_valid():
            try:
                # 5. DATABASE TRANSACTION (Requirement 5)
                # This ensures that if anything fails during the save process, 
                # no partial data is written to the DB.
                with transaction.atomic():
                    # We use a 'select_for_update' logic inside the serializer/model 
                    # to lock the rows and prevent race conditions.
                    booking = serializer.save(
                        
                        booked_by=request.user,
                        status=BookingStatus.CONFIRMED # 7. STATUS SYSTEM
                    )

                return Response({
                    "message": "Booking created successfully",
                    "data": BookingSerializer(booking).data
                }, status=201)

            except serializers.ValidationError as e:
                # 10. ERROR HANDLING (Catching specific domain errors)
                return Response({
                    "error": "Booking failed",
                    "detail": str(e)
                }, status=400)

        # Returns detailed errors (Overlap, Expired, etc.)
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

    def get(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug)

        bookings = Booking.objects.filter(tenant=tenant).order_by("-date")

        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)      


        
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Service
from .serializers import ServiceSerializer


class GlobalServiceListView(APIView):

    permission_classes = []

    def get(self, request):

        query = request.GET.get("search", "")

        services = Service.objects.all()

        if query:
            services = services.filter(
                name__icontains=query
            )

        serializer = ServiceSerializer(
            services,
            many=True
        )

        return Response(serializer.data)        