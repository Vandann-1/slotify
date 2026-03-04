from rest_framework import serializers
from tenants.models import Tenant, TenantMember
from tenants.choices import TenantMemberRole


class TenantSerializer(serializers.ModelSerializer):
    myrole = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "tenant_type",
            "workspace_type",
            "team_size",
            "slug",
            "email",
            "phone",
            "created_at",
            "myrole",
        ]
        read_only_fields = ["id", "slug", "created_at"]

    def get_myrole(self, obj):
        user = self.context["request"].user

        membership = TenantMember.objects.filter(
            tenant=obj,
            user=user,
            removed_at__isnull=True,
        ).first()

        return membership.role if membership else None

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        tenant = Tenant.objects.create(
            owner=user,
            **validated_data,
        )

        # ALWAYS create owner membership
        TenantMember.objects.create(
            tenant=tenant,
            user=user,
            role=TenantMemberRole.OWNER,
        )

        return tenant