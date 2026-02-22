from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer , LoginSerializer
from tenants.models import Tenant


class RegisterView(APIView):
    """
    Register new user.

    IMPORTANT:
    - Registration only creates user
    - Workspace creation happens separately
    """

    permission_classes = [AllowAny]

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



from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken




class LoginView(APIView):
    """
    LoginView

    PURPOSE:
    • Authenticate user
    • Issue JWT tokens
    • Return role-aware payload
    • Provide tenant context for admins
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

    permission_classes = [IsAuthenticated]

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
