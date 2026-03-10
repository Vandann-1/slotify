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
from plans_subsci.models import Plans , Subscription
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from django.utils import timezone

from tenants.models.tenant import Tenant
from tenants.models import TenantMember
from tenants.choices import TenantMemberRole
from tenants.serializers import TenantSerializer

from django.contrib.auth import get_user_model

User = get_user_model()



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
    # INTERNAL HELPERS
    # =====================================================

    def _get_membership(self, tenant, user):
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

        tenant = serializer.save()

        free_plan, _ = Plans.objects.get_or_create(
            name="Free",
            defaults={
                "price": 0,
                "member_limit": 3,
                "description": "Free plan",
                "is_active": True,
            },
        )

        Subscription.objects.create(
            tenant=tenant,
            plan=free_plan
        )

        TenantMember.objects.create(
            tenant=tenant,
            user=self.request.user,
            role=TenantMemberRole.OWNER,
            invited_by=self.request.user,
        )

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

        requester_member = self._get_membership(tenant, requester)
        self._require_admin_or_owner(requester_member)

        plan = tenant.subscription.plan

        member_count = TenantMember.objects.filter(
            tenant=tenant,
            is_active=True
        ).count()

        if plan.member_limit and member_count >= plan.member_limit:
            raise ValidationError(
                f"Member limit reached for {plan.name} plan."
            )

        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            raise ValidationError("User does not exist.")

        existing_member = TenantMember.objects.filter(
            tenant=tenant,
            user=target_user,
        ).first()

        if existing_member and existing_member.is_active:
            raise ValidationError("User is already a member.")

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
            raise ValidationError("Member not found.")

        if target_member.role == TenantMemberRole.OWNER:
            raise PermissionDenied("Owner cannot be removed.")

        target_member.is_active = False
        target_member.removed_at = timezone.now()

        target_member.save(update_fields=["is_active", "removed_at"])

        return Response({"message": "Member removed successfully."})

    # =====================================================
    # MEMBERS LIST (FIXED PLAN LOGIC)
    # =====================================================

    @action(detail=True, methods=["get"])
    def members(self, request, slug=None):

        tenant = self.get_object()

        self._get_membership(tenant, request.user)

        members_qs = (
            TenantMember.objects.filter(
                tenant=tenant,
                is_active=True,
            ).select_related("user")
        )

        members_data = [
            {
                "id": str(member.id),
                "email": member.user.email,
                "role": member.role,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "user_id": member.user.id,
            }
            for member in members_qs
        ]

        members_used = members_qs.count()

        try:
            subscription = tenant.subscription
            plan = subscription.plan

            plan_name = plan.name
            member_limit = plan.member_limit
            members_remaining = max(member_limit - members_used, 0)

        except Subscription.DoesNotExist:
            plan_name = None
            member_limit = None
            members_remaining = None

        return Response(
            {
                "plan": plan_name,
                "member_limit": member_limit,
                "members_used": members_used,
                "members_remaining": members_remaining,
                "members": members_data,
            }
        )

    # =====================================================
    # SUBSCRIPTION INFO
    # =====================================================

    @action(detail=True, methods=["get"])
    def subscription(self, request, slug=None):

        tenant = self.get_object()

        self._get_membership(tenant, request.user)

        subscription = tenant.subscription
        plan = subscription.plan

        return Response({
            "plan": plan.name,
            "price": plan.price,
            "member_limit": plan.member_limit,
            "features": plan.features,
            "start_date": subscription.start_date,
            "is_active": subscription.is_active
        })