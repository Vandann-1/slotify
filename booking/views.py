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
from Backend.permissions import IsTenantOwner, IsTenantAdmin, IsTenantMember
from django.db import transaction
from booking.services import create_booking_service
from rest_framework import serializers
from .serializers import *
from .services import create_booking_service, cancel_booking_service


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
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    def post(self, request, slug):

        tenant = get_object_or_404(Tenant, slug=slug)
        serializer = ServiceSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(tenant=tenant)

            return Response(serializer.data,status=201)
        return Response(serializer.errors,status=400 )



class AvailabilityCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug)
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
    '''1. This view retrieves available time slots for a specific service on a given date.
       2. It first validates the input parameters (service_id and date).'''
    permission_classes = [IsAuthenticated]
    def get(self, request, slug):
        data = get_available_slots(
            slug=slug,
            service_id=request.GET.get("service_id"),
            date_str=request.GET.get("date")
        )
        status_code = data.pop("status", 200)

        return Response(
            data,
            status=status_code
        )
    




class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):

        try:

            booking = create_booking_service(
                request=request,
                slug=slug,
                data=request.data
            )

            return Response({
                "message": "Booking created successfully",
                "data": BookingSerializer(booking).data
            }, status=201)

        except serializers.ValidationError as e:

            return Response(
                e.detail,
                status=400
            )


class CancelBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug, booking_id):
        try:

            booking = Booking.objects.select_related(
                "tenant",
                "provider",
                "customer"
            ).get(
                id=booking_id,
                tenant__slug=slug,
                is_deleted=False
            )

        except Booking.DoesNotExist:

            return Response(
                {"error": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CancelBookingSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data.get(
            "reason",
            ""
        )

        try:

            booking = cancel_booking_service(
                user=request.user,
                booking=booking,
                reason=reason
            )

        except serializers.ValidationError as e:

            return Response(
                e.detail,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({

            "message":
            "Booking cancelled successfully",

            "booking_id":
            str(booking.id),

            "status":
            booking.status,

            "cancelled_by":
            booking.cancelled_by,

            "cancelled_at":
            booking.cancelled_at,

        }, status=status.HTTP_200_OK)
    



class BookingListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

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




class MyBookingsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        bookings = Booking.objects.select_related(
            "tenant",
            "service",
            "provider",
        ).filter(
            customer=request.user,
            is_deleted=False
        ).order_by("-date", "-start_time")

        serializer = BookingSerializer(
            bookings,
            many=True
        )

        return Response(serializer.data)


