from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


from rest_framework import serializers
# from .models import User


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    role = serializers.ChoiceField(
        choices=[("admin", "Admin"), ("client", "Client")],
        default="admin"
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "username",
            "email",
            "password",
            "role"
        ]


    # ============================
    # VALIDATE USERNAME
    # ============================

    def validate_username(self, value):

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Username already exists"
            )

        return value


    # ============================
    # VALIDATE EMAIL
    # ============================

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists"
            )

        return value


    # ============================
    # CREATE USER (FIXED)
    # ============================

    def create(self, validated_data):

        password = validated_data.pop("password")

        role = validated_data.pop("role", "client")

        user = User.objects.create_user(

            username=validated_data["username"],

            email=validated_data["email"],

            full_name=validated_data["full_name"],

            password=password,

            role=role

        )

        return user


# from django.contrib.auth import authenticate
# from rest_framework import serializers

class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):

        user = authenticate(
            username=data["username"],
            password=data["password"]
        )

        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid username or password"]}
            )

        data["user"] = user
        return data
