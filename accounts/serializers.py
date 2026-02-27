from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


from django.contrib.auth import get_user_model


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    RegisterSerializer

    PURPOSE:
    • Create new user safely
    • Enforce unique email & username
    • Normalize email
    • Hash password properly
    """

    password = serializers.CharField(write_only=True)

    role = serializers.ChoiceField(
        choices=[("admin", "Admin"), ("client", "Client")],
        default="admin",
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "username",
            "email",
            "password",
            "role",
        ]

    # ============================
    # VALIDATE USERNAME
    # ============================
    def validate_username(self, value):
        value = value.strip()

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists")

        return value

    # ============================
    # VALIDATE EMAIL
    # ============================
    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")

        return value

    # ============================
    # CREATE USER (CLEAN)
    # ============================
    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role", "admin")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"].lower().strip(),
            full_name=validated_data["full_name"],
            password=password,
        )

        # ✅ only if your User model has role field
        if hasattr(user, "role"):
            user.role = role
            user.save(update_fields=["role"])

        return user




from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

# User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data["email"].lower().strip()
        password = data["password"]

        # ================= FIND USER BY EMAIL =================
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid email or password"]}
            )

        # ================= AUTHENTICATE USING USERNAME =================
        user = authenticate(
            username=user_obj.username,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid email or password"]}
            )

        data["user"] = user
        return data




from .models import ProfessionalProfile


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    """
    Professional's own profile serializer.
    Used when PROFESSIONAL user updates their profile.
    """


    '''this email field is read only and sourced from the related User model,
    so it will be included in the serialized output but cannot be modified through this serializer.'''
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ProfessionalProfile
        fields = [
            "id",
            "email",
            "qualifications",
            "specialization",
            "experience_years",
            "bio",
            "linkdin_url",
            "profile_completed",
            "verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "verified",
            "profile_completed",
            "created_at",
            "updated_at",
        ]

    # ===== VALIDATION =====
    def validate_years_of_experience(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Years of experience cannot be negative."
            )
        if value > 60:
            raise serializers.ValidationError(
                "Years of experience looks unrealistic."
            )
        return value

    # ===== AUTO PROFILE COMPLETION =====
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        important_fields = [
            instance.qualifications,
            instance.specialization,
            instance.experience_years,
        ]

        if all(important_fields):
            if not instance.profile_completed:
                instance.profile_completed = True
                instance.save(update_fields=["profile_completed"])

        return instance