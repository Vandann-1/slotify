from rest_framework import serializers

from .models import TenantInvitation
from .choices import InvitationStatus
from tenants.choices import TenantMemberRole
from tenants.models import TenantMember


from rest_framework import serializers


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField(required=True)
        
class InviteProfessionalSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=TenantMemberRole.choices,
        default=TenantMemberRole.PROFESSIONAL,
    )
     
class ValidateInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField(required=True)        


