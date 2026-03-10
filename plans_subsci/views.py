from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Plans , Subscription
from rest_framework.decorators import action
from .serializers import PlanSerializer , SubscriptionSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here.




class PlanListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plans.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    
    
    
    
    
''' This viewset is for handling subscription related actions. It has two main functions:
1. list: This function retrieves the subscription details of the tenant associated with the authenticated user and returns it in the response.
2. upgrade: This function allows the tenant to upgrade their subscription plan. It takes a plan_id from the request data, checks if the plan exists, and if it does, it updates the tenant's subscription with the new plan and returns the updated subscription details in the response.'''

from tenants.models.tenant import Tenant


class SubscriptionListViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    def list(self, request):

        slug = request.query_params.get("workspace")

        if not slug:
            return Response({"error": "workspace slug required"}, status=400)

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"error": "workspace not found"}, status=404)

        subscription = tenant.subscription

        serializer = SubscriptionSerializer(subscription)

        return Response(serializer.data)    
    
    
    '''in short this def is for upgrading the plan 
    of the tenant and saving the subscription
    with the new plan'''
    @action(detail=False, methods=["post"])
    def upgrade(self, request):

        tenant = request.user.tenant

        plan_id = request.data.get("plan_id")

        try:
            plan = Plans.objects.get(id=plan_id)
        except Plans.DoesNotExist:
            return Response({"error": "Plan not found"}, status=404)

        subscription = tenant.subscription

        subscription.plan = plan
        subscription.save()

        serializer = SubscriptionSerializer(subscription)

        return Response(serializer.data)