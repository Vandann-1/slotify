from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAdminUser , IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer , LoginSerializer , ProfessionalProfileSerializer
from tenants.models import Tenant , TenantMember , TenantMemberRole
from .models import ProfessionalProfile
from rest_framework.generics import RetrieveAPIView
from django.shortcuts import get_list_or_404, get_object_or_404
from django.contrib.auth import get_user_model

from google.oauth2 import id_token
from google.auth.transport import requests
from tenants.choices import *
from tenants.models import (TenantMember,
                            TenantMemberRole)



User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        print("REGISTER HIT")
        serializer = RegisterSerializer(data=request.data,

           context={
                "role": "client"
            }
        )

        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({

                "message":
                "Registration successful",

                "access":
                str(refresh.access_token),

                "refresh":
                str(refresh),

                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },

                "workspace": {
                    "exists": False,
                    "slug": None,
                }

            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from tenants.models import Tenant
from .serializers import RegisterSerializer
from django.utils.text import slugify

class AdminRegisterView(APIView):
    """
    Admin Registration Flow

    FLOW:
    • Create user
    • Create tenant/workspace
    • Create OWNER membership
    • Return JWT + workspace context
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data,
            context={
                # optional now
                # can keep or remove later
                "role": "admin"
            }
        )

        serializer.is_valid(raise_exception=True)

        with transaction.atomic():

            # =================================================
            # CREATE USER
            # =================================================
            user = serializer.save()

            # =================================================
            # CREATE WORKSPACE / TENANT
            # =================================================
            tenant = Tenant.objects.create(

                owner=user,

                name=f"{user.full_name}'s Workspace",

                slug=f"{slugify(user.username)}-{str(user.id)[:6]}"
            )

            # =================================================
            # CREATE OWNER MEMBERSHIP
            # =================================================
            membership = TenantMember.objects.create(

                tenant=tenant,

                user=user,

                role=TenantMemberRole.OWNER,

                invited_by=user,

                is_active=True,
            )

            # =================================================
            # GENERATE JWT TOKENS
            # =================================================
            refresh = RefreshToken.for_user(user)

        # =====================================================
        # FINAL RESPONSE
        # =====================================================
        return Response({

            "message": "Admin registration successful",

            # JWT
            "access": str(refresh.access_token),
            "refresh": str(refresh),

            # USER
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },

            # MEMBERSHIP
            "membership": {
                "role": membership.role,
            },

            # WORKSPACE
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
            }

        }, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        # ================= VALIDATE =================
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # ================= TOKENS =================
        refresh = RefreshToken.for_user(user)

        # ================= MEMBERSHIP =================
        membership = (
            TenantMember.objects
            .filter(
                user=user,
                is_active=True
            )
            .select_related("tenant")
            .first()
        )

        # ================= ROLE FLAGS =================
        role = membership.role if membership else "client"

        is_owner = role == "OWNER"
        is_admin = role == "ADMIN"
        is_professional = role == "PROFESSIONAL"
        is_client = membership is None

        # ================= TENANT =================
        tenant_data = None

        if membership and membership.tenant:

            tenant = membership.tenant

            tenant_data = {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "template": tenant.template_type,
            }

        # ================= RESPONSE =================
        return Response({

            "message": "Login successful",

            # JWT
            "access": str(refresh.access_token),
            "refresh": str(refresh),

            # USER
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
            },

            # MEMBERSHIP
            "membership": {
                "role": role,
                "is_owner": is_owner,
                "is_admin": is_admin,
                "is_professional": is_professional,
                "is_client": is_client,
            },

            # TENANT
            "tenant": tenant_data,

        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    LogoutView

    PURPOSE:
    • Blacklist refresh token
    • Secure logout for JWT users
    """

    permission_classes = [IsAuthenticated] # we can allow any because the token is what authenticates, but it makes sense to require authentication for logout.

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"detail": "Refresh token required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"detail": "Logout successful"},
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )



class ProfessionalProfileView(APIView):
    """
    ProfessionalProfileView

    PURPOSE:
    • Allow professionals to view/update their profile
    • Role-based access control
    here we allow professionals to view and update their profile.
    The get method retrieves the profile, while the put/patch methods allow for updating it.
        We use get_or_create to ensure that a profile always exists for the user, which simplifies frontend logic.
    """

    permission_classes = [IsAuthenticated]
    # simple get is used to fetch the profile, and put/patch to update it.
    def get(self, request):
        profile, _ = ProfessionalProfile.objects.get_or_create(
            user=request.user
        )
        serializer = ProfessionalProfileSerializer(profile)
        return Response(serializer.data)
    # simple put is used to update the profile, and patch is also supported for partial updates.
    def put(self, request):
        profile, _ = ProfessionalProfile.objects.get_or_create(
            user=request.user
        )
        serializer = ProfessionalProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # optional but nice
    def patch(self, request):
        return self.put(request)
    
    
    
class AdminProfessionalDetailView(RetrieveAPIView):
    ''' this view allows admins to view any professional's profile by user ID.
    This is useful for admin dashboards where admins need to manage professionals.
    The view is protected by IsAuthenticated, but in a real application you might
    want to add an additional check to ensure the user is an admin.
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # auto-healing
        profile, _ = ProfessionalProfile.objects.get_or_create(
            user=user
        )

        serializer = ProfessionalProfileSerializer(profile)
        return Response(serializer.data)    
    
 


User = get_user_model()

GOOGLE_CLIENT_ID = "17036355569-kqo9lo3vmjli90a59qdk7p0v3g4qovjr.apps.googleusercontent.com"


class GoogleLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        token = request.data.get("token")

        if not token:
            return Response({"detail": "Token missing"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request()
            )

            if idinfo["aud"] != GOOGLE_CLIENT_ID:
                return Response({"detail": "Invalid audience"}, status=400)

            email = idinfo["email"]

        except Exception as e:
            print("GOOGLE ERROR:", e)
            return Response({"detail": "Invalid Google token"}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email}
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email
            }
        })