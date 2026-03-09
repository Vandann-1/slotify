from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Plans , Subscription
from rest_framework.views import APIView
from .serializers import PlanSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here.


class PlanListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self , request):
        plans = Plans.objects.filter(isactive_plan=True)
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)
    