from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer


class RegisterView(APIView):
    
    permission_classes = [AllowAny]   # ← ADD THIS

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            return Response({

                "message": "User registered successfully",

                "user": {

                    "id": user.id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "email": user.email,

                }

            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    permission_classes = [AllowAny]


    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            return Response({

                "message": "Login successful",

                "access": str(refresh.access_token),

                "refresh": str(refresh),

                "user": {

                    "id": user.id,
                    "email": user.email,
                    "username": user.username,

                }

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
