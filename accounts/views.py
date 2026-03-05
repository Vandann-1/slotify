from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAdminUser , IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer , LoginSerializer , ProfessionalProfileSerializer
from tenants.models import Tenant
from .models import ProfessionalProfile
from rest_framework.generics import RetrieveAPIView
from django.shortcuts import get_list_or_404, get_object_or_404
from django.contrib.auth import get_user_model

from google.oauth2 import id_token
from google.auth.transport import requests





User = get_user_model()

class RegisterView(APIView):
    """
    Register new user.

    IMPORTANT:
    - Registration only creates user
    - Workspace creation happens separately
    
    """

    permission_classes = [AllowAny] # open to all for registration

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            # ==============================
            # CREATE USER
            # ==============================
            user = serializer.save()

            # ==============================
            # GENERATE JWT
            # ==============================
            refresh = RefreshToken.for_user(user)

            # ==============================
            # RESPONSE
            # ==============================
            return Response({
                "message": "Registration successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "tenant": None  # no auto workspace
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )






class LoginView(APIView):
    """
    LoginView

    PURPOSE:
    • Authenticate user
    • Issue JWT tokens
    • Return role-aware payload
    • Provide tenant context for admins
    
    this is the main login view for the application.
    It handles user authentication and returns a JWT token along
    with user information and tenant context if applicable.
    The view checks the user's role to determine if 
    they are an admin and if they own a tenant, which is included
    in the response. This allows the frontend to easily 
    manage user sessions and display relevant information 
    based on the user's role and workspace context.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # ================= JWT =================
        refresh = RefreshToken.for_user(user)

        # ================= TENANT CONTEXT =================
        tenant_data = None

        # Only admins own tenants
        if getattr(user, "role", None) == "admin":
            tenant = Tenant.objects.filter(owner=user).first()

            if tenant:
                tenant_data = {
                    "id": tenant.id,
                    "name": tenant.name,
                    "tenant_type": tenant.tenant_type,
                }

        # ================= ROLE FLAGS (VERY USEFUL) =================
        is_admin = getattr(user, "role", None) == "admin"
        is_client = getattr(user, "role", None) == "client"

        # ================= RESPONSE =================
        return Response(
            {
                "message": "Login successful",

                # tokens
                "access": str(refresh.access_token),
                "refresh": str(refresh),

                # user info
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                    "is_admin": is_admin,
                    "is_client": is_client,
                },

                # workspace context
                "tenant": tenant_data,
            },
            status=status.HTTP_200_OK,
        )


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