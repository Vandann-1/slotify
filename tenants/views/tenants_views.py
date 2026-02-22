from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from tenants.models import Tenant, TenantMember
from tenants.serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    """
    Tenant ViewSet

    Responsibilities:
    - List workspaces for current user
    - Create workspace
    - Workspace dashboard access
    - Professional memberships feed
    - List workspace members (NEW)
    """

    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    # =====================================================
    # WORKSPACE LIST
    # =====================================================
    def get_queryset(self):
        """
        Return only workspaces where the current user is an active member.
        """
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("Login to view your workspaces.")

        return Tenant.objects.filter(
            members__user=user,
            is_active=True
        ).distinct()

    # =====================================================
    # CREATE WORKSPACE
    # =====================================================
    def perform_create(self, serializer):
        """
        When a workspace is created, the request user becomes owner.
        """
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in.")

        serializer.save(owner=user)

    # =====================================================
    # SERIALIZER CONTEXT
    # =====================================================
    def get_serializer_context(self):
        """
        Ensure request is available inside serializer.
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    # =====================================================
    # ADMIN DASHBOARD
    # =====================================================
    @action(detail=True, methods=["get"])
    def dashboard(self, request, slug=None):
        """
        GET /api/workspaces/{slug}/dashboard/

        Allows only workspace members.
        """
        tenant = self.get_object()

        is_member = tenant.members.filter(
            user=request.user,
            is_active=True
        ).exists()

        if not is_member:
            raise PermissionDenied(
                "You are not a member of this workspace."
            )

        return Response({
            "message": f"Welcome to the dashboard of {tenant.name}!"
        })

    # =====================================================
    # PROFESSIONAL MEMBERSHIPS FEED
    # =====================================================
    @action(detail=False, methods=["get"], url_path="my-memberships")
    def my_memberships(self, request):
        """
        GET /api/workspaces/my-memberships/

        Returns all workspaces where current user is a member.
        Used by Professional Dashboard.
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

    # =====================================================
    # WORKSPACE MEMBERS (CRITICAL — NEW)
    # =====================================================
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, slug=None):
        """
        GET /api/workspaces/{slug}/members/

        Returns all active members of a workspace.
        Used by TeamMembers panel.
        """

        tenant = self.get_object()

        # Security: only members can view team
        is_member = tenant.members.filter(
            user=request.user,
            is_active=True
        ).exists()

        if not is_member:
            raise PermissionDenied(
                "You are not allowed to view members of this workspace."
            )

        members_qs = TenantMember.objects.filter(
            tenant=tenant,
            is_active=True
        ).select_related("user")

        data = [
            {
                "id": str(member.id),
                "email": member.user.email,
                "role": member.role,
                "joined_at": member.joined_at,
            }
            for member in members_qs
        ]

        return Response(data)