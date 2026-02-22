"""
invitations/api.py

Handles:
1. Accepting an invitation via token
2. Sending an invitation to a professional

Flow:
- Invite endpoint creates invitation
- Accept endpoint validates token and creates membership
"""

from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from tenants.models.tenant import Tenant
from tenants.models import TenantMember
from invitations.models import TenantInvitation
from invitations.choices import InvitationStatus
from invitations.serializers import (
    AcceptInvitationSerializer,
    InviteProfessionalSerializer,
    ValidateInvitationSerializer
)


User = get_user_model()


# ============================================================================
# ACCEPT INVITATION API
# ============================================================================



class AcceptInvitationAPIView(APIView):
    """
    AcceptInvitationAPIView

    PURPOSE:
    • Authenticated user accepts an invitation
    • Creates TenantMember safely
    • Prevents reuse and race conditions
    • Enforces email ownership security

    SECURITY LEVEL: Production-safe
    """

    # 🚨 User MUST be logged in
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """
        Accept invitation endpoint

        Flow:
        1. Validate request body
        2. Lock invitation row
        3. Check expiry
        4. Check status
        5. Verify email ownership (CRITICAL)
        6. Create membership if needed
        7. Mark invitation accepted
        """

        # ================= STEP 1 — Validate payload =================
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        # ================= STEP 2 — Fetch invitation with DB lock =================
        invitation = get_object_or_404(
            TenantInvitation.objects.select_for_update(),
            token=token,
        )

        user = request.user

        # 🔍 DEBUG (remove in production if noisy)
        # print("LOGGED USER:", user.email)
        # print("INVITE EMAIL:", invitation.email)

        # ================= STEP 3 — Expiry guard =================
        if invitation.is_expired():
            invitation.status = InvitationStatus.EXPIRED
            invitation.save(update_fields=["status"])

            return Response(
                {"detail": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ================= STEP 4 — Prevent reuse =================
        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"detail": "Invitation already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ================= STEP 5 — CRITICAL SECURITY CHECK =================
        # Only the invited email owner can accept
        if invitation.email.strip().lower() != user.email.strip().lower():
            raise PermissionDenied(
                f"This invite was sent to {invitation.email}. "
                "Please login with that account."
            )

        # ================= STEP 6 — Prevent duplicate membership =================
        member_exists = TenantMember.objects.filter(
            tenant=invitation.tenant,
            user=user,
        ).exists()

        if not member_exists:
            TenantMember.objects.create(
                tenant=invitation.tenant,
                user=user,
                role=invitation.role,
                invited_by=invitation.invited_by,
            )

        # ================= STEP 7 — Mark invitation accepted =================
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at"])

        # ================= SUCCESS RESPONSE =================
        return Response(
            {"detail": "Invitation accepted successfully."},
            status=status.HTTP_200_OK,
        )

# ============================================================================
# INVITE PROFESSIONAL API
# ============================================================================
@method_decorator(csrf_exempt, name='dispatch')
class InviteProfessionalAPIView(APIView):
    """
    Invite a professional to a tenant workspace.

    POST /api/invitations/workspaces/<slug>/invite/
    Body: { "email": "...", "role": "..." }
    """

    # NOTE: Should be IsAuthenticated in production
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, slug):
        # -------------------------------
        # Validate input
        # -------------------------------
        serializer = InviteProfessionalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower().strip()
        role = serializer.validated_data["role"]

        # -------------------------------
        # Fetch tenant
        # -------------------------------
        tenant = get_object_or_404(Tenant, slug=slug)

        # -------------------------------
        # Check if user already member
        # -------------------------------
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            already_member = TenantMember.objects.filter(
                tenant=tenant,
                user=existing_user,
                is_active=True,
            ).exists()

            if already_member:
                return Response(
                    {"detail": "User is already a member."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # -------------------------------
        # Prevent duplicate pending invite
        # -------------------------------
        existing_invite = TenantInvitation.objects.filter(
            tenant=tenant,
            email__iexact=email,
            status=InvitationStatus.PENDING,
        ).first()

        if existing_invite:
            return Response(
                {"detail": "Pending invitation already exists."},
                status=status.HTTP_200_OK,
            )

        # -------------------------------
        # Create invitation
        # -------------------------------
        invitation = TenantInvitation.objects.create(
            tenant=tenant,
            invited_by=tenant.owner,
            email=email,
            role=role,
            status=InvitationStatus.PENDING,
        )

        return Response(
            {
                "detail": "Invitation sent successfully.",
                "token": str(invitation.token),  # remove after email integration
            },
            status=status.HTTP_201_CREATED,
        )
        
        
class ValidateInvitationAPIView(APIView):
    """
    Public endpoint to validate invitation token.

    POST /api/invitations/validate/
    Body: { "token": "<uuid>" }
    """

    permission_classes = []  # public

    def post(self, request):
        serializer = ValidateInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        invitation = TenantInvitation.objects.filter(
            token=token,
            status=InvitationStatus.PENDING,
        ).select_related("tenant").first()

        if not invitation:
            return Response(
                {"valid": False, "detail": "Invalid or expired invitation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "valid": True,
                "tenant": invitation.tenant.name,
                "email": invitation.email,
                "role": invitation.role,
            },
            status=status.HTTP_200_OK,
        )        