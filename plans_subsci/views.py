from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Plans, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from tenants.models.tenant import Tenant


class PlanListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns all active subscription plans.
    """
    queryset = Plans.objects.filter(is_active=True).order_by("price")
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]


class SubscriptionListViewSet(viewsets.ViewSet):
    """
    Handles subscription related actions:
    - View current workspace subscription
    - Upgrade workspace plan
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get subscription details for a workspace.
        Example:
        GET /api/subscription/?workspace=it-club
        """

        slug = request.query_params.get("workspace")

        if not slug:
            return Response(
                {"error": "workspace slug required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"error": "workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = tenant.subscription
        serializer = SubscriptionSerializer(subscription)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def upgrade(self, request):
        """
        Upgrade workspace subscription plan.

        POST /api/subscription/upgrade/

        Body:
        {
            "workspace": "it-club",
            "plan_id": 2
        }
        """

        slug = request.data.get("workspace")
        plan_id = request.data.get("plan_id")

        if not slug or not plan_id:
            return Response(
                {"error": "workspace and plan_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"error": "workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            plan = Plans.objects.get(id=plan_id, is_active=True)
        except Plans.DoesNotExist:
            return Response(
                {"error": "plan not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = tenant.subscription
        subscription.plan = plan
        subscription.save()

        serializer = SubscriptionSerializer(subscription)

        return Response(
            {
                "message": "Subscription upgraded successfully",
                "subscription": serializer.data
            },
            status=status.HTTP_200_OK
        )