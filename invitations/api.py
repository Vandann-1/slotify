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
from rest_framework.permissions import AllowAny


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
    For REACT APP, this endpoint is called when user clicks "Accept Invite"
    link in email, which includes the token.
    User must be logged in with the same email to accept.
    url pattern: POST /api/invitations/accept/
    
    """

    # User MUST be logged in
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """
        Accept invitation endpoint
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

        # =================  NEW — Sync user platform role =================
        current_role = (user.role or "").lower()
        PROFESSIONAL_ROLES = {"professional", "member", "pro"}

        if invitation.role and invitation.role.lower() in PROFESSIONAL_ROLES:
            if current_role not in PROFESSIONAL_ROLES:
                user.role = invitation.role.lower()
                user.save(update_fields=["role"])

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
from django.core.mail import send_mail
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class InviteProfessionalAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, slug):

        serializer = InviteProfessionalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower().strip()
        role = serializer.validated_data["role"]

        tenant = get_object_or_404(Tenant, slug=slug)

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

        invitation = TenantInvitation.objects.create(
            tenant=tenant,
            invited_by=tenant.owner,
            email=email,
            role=role,
            status=InvitationStatus.PENDING,
        )

        # Create invite link
        invite_link = f"{settings.FRONTEND_URL}/invite-accept/{invitation.token}"

        # Email message
        message = f"""
            Slotify | Workspace Invitation

                You're moving up. You’ve been invited to collaborate within the "{tenant.name}" environment.

                    Click below to sync with your team and scale your workflow:

                        Log In & Accept: {invite_link}

            If this wasn't intended for you, no action is required.
"""

        # Send email
        send_mail(
            subject=f"Invitation to join {tenant.name}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {
                "detail": "Invitation sent successfully.",
                "token": str(invitation.token),
            },
            status=status.HTTP_201_CREATED,
        )        
        
class ValidateInvitationAPIView(APIView):
    """
    Public endpoint to validate invitation token.
    this is used by the frontend to check if the token in the invite link
    is valid before showing the accept invite UI.

    url pattern: POST /api/invitations/validate/
    Body: { "token": "<uuid>" }
    """

    permission_classes = [AllowAny] 
    authentication_classes=[]# public

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