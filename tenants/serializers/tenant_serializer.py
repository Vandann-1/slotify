from rest_framework import serializers
from tenants.models import Tenant, TenantMember
from tenants.choices import TenantMemberRole


class TenantSerializer(serializers.ModelSerializer):
    
    '''this is a serializer for tenant model.
       it will be used to create and update tenants.
       it will also be used to list tenants.
       POST /api/workspaces/ - create a new tenant
       GET /api/workspaces/ - list all tenants of the user
       from react side we will use this serializer to create and list tenants.
       step 1: user will fill the form and submit it.
       step 2: we will send a POST request to /api/workspaces/ with the
               form data and the user token.
       step 3: if the request is successful we will get the tenant data in response.'''
    
    # this my role is used to show the role of the user in the tenant.
    myrole=serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "tenant_type",
            "slug",
            "email",
            "phone",
            "team_size",
            "created_at",
            "myrole"
        ]
        read_only_fields = ["id", "slug", "created_at"]

    def get_myrole(self, obj):

        user = self.context["request"].user

        
        tenant_member = TenantMember.objects.filter(
            tenant=obj,
            user=user
        ).first()

        if tenant_member:
            return tenant_member.role

        return None
    
    '''this method is used to create a tenant 
          and also create a tenant member
             with the role of owner.'''
    
    def create(self, validated_data):
        
        req = self.context.get("request")
        
        user = req.user if req else None

        owner = validated_data.pop("owner")

        tenant = Tenant.objects.create(
            owner=owner,
            **validated_data
        )

        TenantMember.objects.create(
            tenant=tenant,
            user=owner,
            role=TenantMemberRole.OWNER
        )

        return tenant
