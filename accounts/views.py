from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer , LoginSerializer

from tenants.models import Tenant


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            # Create user
            user = serializer.save()

            tenant = None


            # ====================================
            # CREATE TENANT FOR ADMIN
            # ====================================

            if user.role == "admin":

                tenant = Tenant.objects.create(

                    name=f"{user.username}'s Workspace",

                    tenant_type="personal",  # must match your TenantType choices

                    email=user.email,

                    owner=user

                )


            # ====================================
            # GENERATE JWT TOKEN
            # ====================================

            refresh = RefreshToken.for_user(user)


            # ====================================
            # RESPONSE
            # ====================================

            return Response({

                "message": "Registration successful",

                "access": str(refresh.access_token),

                "refresh": str(refresh),

                "user": {

                    "id": user.id,

                    "username": user.username,

                    "email": user.email,

                    "role": user.role

                },

                # include tenant if admin
                "tenant": {

                    "id": tenant.id,

                    "name": tenant.name,

                    "tenant_type": tenant.tenant_type

                } if tenant else None

            }, status=status.HTTP_201_CREATED)


        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )





class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            # get tenant if admin
            tenant = None

            if user.role == "admin":

                tenant = Tenant.objects.filter(
                    owner=user
                ).first()


            return Response({

                "message": "Login successful",

                "access": str(refresh.access_token),

                "refresh": str(refresh),

                "user": {

                    "id": user.id,

                    "email": user.email,

                    "username": user.username,

                    "role": user.role,

                },

                # tenant info for admin
                "tenant": {

                    "id": tenant.id,

                    "name": tenant.name,

                    "tenant_type": tenant.tenant_type,

                } if tenant else None

            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )        

class LogoutView(APIView):

    def post(self, request):

        return Response({

            "message": "Logout successful"

        }, status=status.HTTP_200_OK)
