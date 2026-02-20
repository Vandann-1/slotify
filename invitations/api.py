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
from rest_framework import status

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
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()


# ============================================================================
# ACCEPT INVITATION API
# ============================================================================

# from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import get_object_or_404
# from django.db import transaction
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# from .models import TenantInvitation, InvitationStatus
# from .serializers import AcceptInvitationSerializer
# from tenants.models.membership import TenantMember


class AcceptInvitationAPIView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ DRF handles auth

    @transaction.atomic
    def post(self, request):
        # 1️⃣ validate body
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        # 2️⃣ get invitation safely
        invitation = get_object_or_404(
            TenantInvitation.objects.select_for_update(),
            token=token,
        )

        # 3️⃣ check already used
        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"detail": "Invitation already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user  # ✅ guaranteed authenticated

        # 4️⃣ prevent duplicate membership
        member_exists = TenantMember.objects.filter(
            tenant=invitation.tenant,
            user=user,
        ).exists()

        if member_exists:
            invitation.status = InvitationStatus.ACCEPTED
            invitation.save(update_fields=["status"])
            return Response({"detail": "You are already a member."})

        # 5️⃣ create membership
        TenantMember.objects.create(
            tenant=invitation.tenant,
            user=user,
            role=invitation.role,
            invited_by=invitation.invited_by,
        )

        # 6️⃣ mark accepted
        invitation.status = InvitationStatus.ACCEPTED
        invitation.save(update_fields=["status"])

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
    permission_classes = []

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