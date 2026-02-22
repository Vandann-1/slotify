from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from tenants.models import Tenant
from tenants.serializers import TenantSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from tenants.models import TenantMember


class TenantViewSet(viewsets.ModelViewSet):
    """
    Tenant ViewSet
    """

    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    # ================= WORKSPACE LIST =================
    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("Login to view your workspaces.")

        return Tenant.objects.filter(
            members__user=user,
            is_active=True
        ).distinct()

    # ================= CREATE WORKSPACE =================
    def perform_create(self, serializer):
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in.")

        serializer.save(owner=user)

    # ================= SERIALIZER CONTEXT =================
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    # ================= ADMIN DASHBOARD =================
    @action(detail=True, methods=["get"])
    def dashboard(self, request, slug=None):
        tenant = self.get_object()

        # SECURITY: ensure user is member
        is_member = tenant.members.filter(
            user=request.user,
            is_active=True
        ).exists()

        if not is_member:
            raise PermissionDenied("You are not a member of this workspace.")

        return Response({
            "message": f"Welcome to the dashboard of {tenant.name}!"
        })

    # ================= PROFESSIONAL FEED =================
    @action(detail=False, methods=["get"], url_path="my-memberships")
    def my_memberships(self, request):
        """
        Returns all workspaces where current user is a member.

        GET /api/workspaces/my-memberships/
        """

        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied("Login required.")

        memberships = TenantMember.objects.filter(
            user=user,
            is_active=True
        ).select_related("tenant")

        data = [
            {
                "workspace": m.tenant.name,
                "slug": m.tenant.slug,
                "role": m.role,
            }
            for m in memberships
        ]

        return Response(data)