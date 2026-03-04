from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import (
    ValidationError,
    NotFound,
    PermissionDenied,
)

from django.contrib.auth.models import User

from tenants.models import Tenant, TenantMember, TenantMemberRole
from tenants.serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    """
    Tenant ViewSet — production hardened
    
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    # =====================================================
    # INTERNAL HELPERS (VERY IMPORTANT)
    # =====================================================
    def _get_membership(self, tenant, user):
        """Get active membership or raise."""
        try:
            return TenantMember.objects.get(
                tenant=tenant,
                user=user,
                is_active=True,
            )
        except TenantMember.DoesNotExist:
            raise PermissionDenied(
                "You are not a member of this workspace."
            )

    def _require_admin_or_owner(self, membership):
        """Ensure user has admin privileges."""
        if membership.role not in [
            TenantMemberRole.OWNER,
            TenantMemberRole.ADMIN,
        ]:
            raise PermissionDenied(
                "You do not have permission to perform this action."
            )

    # =====================================================
    # WORKSPACE LIST
    # =====================================================
    def get_queryset(self):
        user = self.request.user

        return (
            Tenant.objects.filter(
                members__user=user,
                members__is_active=True,
                is_active=True,
            )
            .distinct()
        )

    # =====================================================
    # CREATE WORKSPACE
    # =====================================================
    def perform_create(self, serializer):
        # Serializer already handles owner creation
        serializer.save()

    # =====================================================
    # DASHBOARD
    # =====================================================
    @action(detail=True, methods=["get"])
    def dashboard(self, request, slug=None):
        tenant = self.get_object()

        self._get_membership(tenant, request.user)

        return Response(
            {"message": f"Welcome to the dashboard of {tenant.name}!"}
        )

    # =====================================================
    # MY MEMBERSHIPS
    # =====================================================
    @action(detail=False, methods=["get"], url_path="my-memberships")
    def my_memberships(self, request):
        memberships = (
            TenantMember.objects.filter(
                user=request.user,
                is_active=True,
            ).select_related("tenant")
        )

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
    # ADD MEMBER
    # =====================================================
    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, slug=None):
        tenant = self.get_object()
        requester = request.user

        target_user_id = request.data.get("user_id")
        role = request.data.get(
            "role", TenantMemberRole.PROFESSIONAL
        )

        if not target_user_id:
            raise ValidationError({"user_id": "This field is required."})

        # requester check
        requester_member = self._get_membership(tenant, requester)
        self._require_admin_or_owner(requester_member)

        # target user
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            raise NotFound("User not found.")

        existing_member = TenantMember.objects.filter(
            tenant=tenant,
            user=target_user,
        ).first()

        # already active
        if existing_member and existing_member.is_active:
            raise ValidationError("User is already a member.")

        # reactivate soft-deleted member
        if existing_member and not existing_member.is_active:
            existing_member.is_active = True
            existing_member.removed_at = None
            existing_member.role = role
            existing_member.invited_by = requester
            existing_member.save(
                update_fields=[
                    "is_active",
                    "removed_at",
                    "role",
                    "invited_by",
                ]
            )
            return Response(
                {"message": "Member reactivated successfully."}
            )

        # create new membership
        TenantMember.objects.create(
            tenant=tenant,
            user=target_user,
            role=role,
            invited_by=requester,
        )

        return Response({"message": "Member added successfully."})

    # =====================================================
    # REMOVE MEMBER
    # =====================================================
    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, slug=None):
        tenant = self.get_object()
        requester = request.user
        target_user_id = request.data.get("user_id")

        if not target_user_id:
            raise ValidationError({"user_id": "This field is required."})

        requester_member = self._get_membership(tenant, requester)
        self._require_admin_or_owner(requester_member)

        try:
            target_member = TenantMember.objects.get(
                tenant=tenant,
                user_id=target_user_id,
                is_active=True,
            )
        except TenantMember.DoesNotExist:
            raise NotFound(
                "Member not found or already removed."
            )

        # prevent owner removal
        if target_member.role == TenantMemberRole.OWNER:
            raise PermissionDenied("Owner cannot be removed.")

        # soft remove
        target_member.is_active = False
        target_member.removed_at = timezone.now()
        target_member.save(update_fields=["is_active", "removed_at"])

        return Response({"message": "Member removed successfully."})

    # =====================================================
    # MEMBERS LIST
    # =====================================================
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, slug=None):
        tenant = self.get_object()

        self._get_membership(tenant, request.user)

        members_qs = (
            TenantMember.objects.filter(
                tenant=tenant,
                is_active=True,
            ).select_related("user")
        )

        data = [
            {
                "id": str(member.id),
                "email": member.user.email,
                "role": member.role,
                "joined_at": member.joined_at.isoformat(),
                "user_id": member.user.id,
            }
            for member in members_qs
        ]

        return Response(data)